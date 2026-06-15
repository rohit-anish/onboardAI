import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import networkx as nx

class GraphifyAdapter:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.graphify_out = self.repo_path / "graphify-out"
        self.graph_path = self.graphify_out / "graph.json"
        self.analysis_path = self.graphify_out / ".graphify_analysis.json"
        self.labels_path = self.graphify_out / ".graphify_labels.json"
        self.manifest_path = self.graphify_out / "manifest.json"
        
        self.graph_data: Dict[str, Any] = {}
        self.analysis_data: Dict[str, Any] = {}
        self.labels_data: Dict[str, str] = {}
        self.manifest_data: Dict[str, Any] = {}
        self.G: Optional[nx.DiGraph] = None

    def generate_graph(self) -> bool:
        """
        Run the graphify extraction process on the repository.
        This triggers 'python -m graphify extract <repo_path>'
        """
        print(f"Triggering Graphify extraction for {self.repo_path}...", file=sys.stderr)
        try:
            # Run the command using the Python executable
            cmd = [sys.executable, "-m", "graphify", "extract", str(self.repo_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout, file=sys.stderr)
            
            # If analysis file wasn't written (e.g. no-cluster defaulted or LLM skipped),
            # trigger cluster-only to name communities and build cohesion metrics.
            if not self.analysis_path.exists():
                cluster_cmd = [sys.executable, "-m", "graphify", "cluster-only", str(self.repo_path)]
                subprocess.run(cluster_cmd, capture_output=True, text=True)
                
            return self.graph_path.exists()
        except Exception as e:
            print(f"Failed to generate graph: {e}", file=sys.stderr)
            return False

    def load_graph(self, auto_generate: bool = True) -> bool:
        """
        Load Graphify files. If they don't exist and auto_generate is True, trigger generation.
        """
        if not self.graph_path.exists():
            if auto_generate:
                success = self.generate_graph()
                if not success:
                    return False
            else:
                return False

        try:
            # Load graph.json
            with open(self.graph_path, "r", encoding="utf-8") as f:
                self.graph_data = json.load(f)
            
            # Load .graphify_analysis.json
            if self.analysis_path.exists():
                with open(self.analysis_path, "r", encoding="utf-8") as f:
                    self.analysis_data = json.load(f)
            else:
                self.analysis_data = {}

            # Load .graphify_labels.json
            if self.labels_path.exists():
                try:
                    with open(self.labels_path, "r", encoding="utf-8") as f:
                        lbl_data = json.load(f)
                        if isinstance(lbl_data.get("labels"), dict):
                            self.labels_data = {str(k): str(v) for k, v in lbl_data["labels"].items()}
                        else:
                            self.labels_data = {str(k): str(v) for k, v in lbl_data.items()}
                except Exception:
                    self.labels_data = {}
            else:
                self.labels_data = {}

            # Load manifest.json
            if self.manifest_path.exists():
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.manifest_data = json.load(f)
            else:
                self.manifest_data = {}

            # Build NetworkX Directed Graph
            self.G = nx.DiGraph()
            
            # Add nodes
            for node in self.graph_data.get("nodes", []):
                node_id = node.get("id")
                if node_id:
                    self.G.add_node(node_id, **node)
            
            # Add links/edges
            links = self.graph_data.get("links", []) or self.graph_data.get("edges", [])
            for link in links:
                src = link.get("source")
                tgt = link.get("target")
                if src and tgt:
                    self.G.add_edge(src, tgt, **link)

            return True
        except Exception as e:
            print(f"Error loading graph: {e}", file=sys.stderr)
            return False

    def get_communities(self) -> Dict[str, Any]:
        """
        Get communities/modules from analysis data.
        Returns a dict of community_id -> {id, label, cohesion, nodes: [node_data]}
        """
        if not self.graph_data:
            return {}

        communities = {}
        analysis_comm = self.analysis_data.get("communities", {})
        
        # Fallback: scan nodes for their community property
        if not analysis_comm and self.G:
            node_comm_map = {}
            for n, d in self.G.nodes(data=True):
                c = d.get("community")
                if c is not None:
                    node_comm_map.setdefault(str(c), []).append(n)
            analysis_comm = node_comm_map

        for cid, node_ids in analysis_comm.items():
            lbl = self.labels_data.get(str(cid)) or f"Community {cid}"
            
            node_details = []
            for nid in node_ids:
                if self.G and self.G.has_node(nid):
                    node_details.append(self.G.nodes[nid])
                else:
                    found = False
                    for n in self.graph_data.get("nodes", []):
                        if n.get("id") == nid:
                            node_details.append(n)
                            found = True
                            break
                    if not found:
                        node_details.append({"id": nid, "label": nid})
            
            communities[str(cid)] = {
                "id": cid,
                "label": lbl,
                "cohesion": self.analysis_data.get("cohesion", {}).get(str(cid), 0.0),
                "nodes": node_details
            }
            
        return communities

    def get_key_components(self) -> List[Dict[str, Any]]:
        """
        Get the most important components (hubs) in the codebase.
        Uses analysis "gods" if available, or calculates degree centrality.
        """
        if self.analysis_data.get("gods"):
            return self.analysis_data["gods"]
            
        if not self.G:
            return []
            
        degree = dict(self.G.degree())
        sorted_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)
        
        key_components = []
        for nid, deg in sorted_nodes:
            node_data = self.G.nodes[nid]
            ftype = node_data.get("file_type", "")
            if ftype in ["file", "rationale", "concept"]:
                continue
            key_components.append({
                "id": nid,
                "label": node_data.get("label", nid),
                "degree": deg,
                "source_file": node_data.get("source_file", ""),
                "description": node_data.get("description", "")
            })
            if len(key_components) >= 10:
                break
        return key_components

    def get_dependencies(self) -> Dict[str, Any]:
        """
        Get project dependencies (both internal calls/imports and external imports).
        """
        if not self.G:
            return {"internal": [], "external": []}
            
        internal_edges = []
        external_deps = set()
        
        for u, v, d in self.G.edges(data=True):
            relation = d.get("relation", "")
            if relation == "imports":
                if v in self.G.nodes:
                    target_node = self.G.nodes[v]
                else:
                    target_node = {}
                
                if target_node.get("file_type") == "external" or not target_node.get("source_file"):
                    external_deps.add(target_node.get("label", v))
                else:
                    internal_edges.append({
                        "source": u,
                        "target": v,
                        "source_label": self.G.nodes[u].get("label", u) if u in self.G.nodes else u,
                        "target_label": self.G.nodes[v].get("label", v) if v in self.G.nodes else v,
                        "relation": "imports",
                        "source_file": d.get("source_file", "")
                    })
            elif relation == "calls":
                internal_edges.append({
                    "source": u,
                    "target": v,
                    "source_label": self.G.nodes[u].get("label", u) if u in self.G.nodes else u,
                    "target_label": self.G.nodes[v].get("label", v) if v in self.G.nodes else v,
                    "relation": "calls",
                    "source_file": d.get("source_file", "")
                })
                
        return {
            "internal": internal_edges,
            "external": list(sorted(external_deps))
        }

    def get_modules(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group codebase entities into modules based on their directory structure.
        """
        if not self.G:
            return {}
            
        modules = {}
        for nid, d in self.G.nodes(data=True):
            sf = d.get("source_file", "")
            if not sf:
                continue
            
            sf_path = Path(sf)
            if len(sf_path.parts) > 1:
                module_name = sf_path.parts[0]
            else:
                module_name = "root"
                
            modules.setdefault(module_name, []).append({
                "id": nid,
                "label": d.get("label", nid),
                "type": d.get("type", d.get("file_type", "unknown")),
                "file": sf
            })
            
        return modules

    def get_project_summary(self) -> Dict[str, Any]:
        """
        Synthesize a high level project summary from the Graphify graph.
        """
        if not self.G:
            return {"error": "Graph not loaded"}
            
        total_nodes = self.G.number_of_nodes()
        total_edges = self.G.number_of_edges()
        
        file_nodes = [n for n, d in self.G.nodes(data=True) if d.get("file_type") == "file"]
        symbol_nodes = [n for n, d in self.G.nodes(data=True) if d.get("file_type") != "file"]
        
        # Get tech stack
        from scanner.architecture_detector import ArchitectureDetector
        detector = ArchitectureDetector(str(self.repo_path))
        arch_details = detector.detect()
        
        # Get key components
        keys = self.get_key_components()
        key_labels = [k["label"] for k in keys]
        
        # Get external dependencies
        deps = self.get_dependencies()
        
        tech_str = ", ".join(arch_details["detected_technologies"]) if arch_details["detected_technologies"] else "unknown technologies"
        arch_type = arch_details["architecture_type"]
        
        summary_text = (
            f"This project is a {arch_type} powered by {tech_str}. "
            f"It consists of {len(file_nodes)} files and {len(symbol_nodes)} code symbols, "
            f"representing {total_nodes} entities and {total_edges} relations in the repository intelligence graph.\n\n"
            f"Core abstractions include: {', '.join(key_labels[:5])}.\n"
            f"Major external dependencies: {', '.join(deps['external'][:8]) if deps['external'] else 'None detected'}."
        )
        
        return {
            "project_name": self.repo_path.name,
            "architecture_type": arch_type,
            "detected_technologies": arch_details["detected_technologies"],
            "key_components": keys[:5],
            "external_dependencies": deps["external"],
            "summary": summary_text,
            "stats": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "file_count": len(file_nodes),
                "symbol_count": len(symbol_nodes)
            }
        }
