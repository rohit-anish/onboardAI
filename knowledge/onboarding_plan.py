from typing import Dict, Any, List, Optional
import networkx as nx
from pathlib import Path
from knowledge.graphify_adapter import GraphifyAdapter

class OnboardingPlanGenerator:
    def __init__(self, adapter: GraphifyAdapter):
        self.adapter = adapter

    def generate(self, role: Optional[str] = None, team: Optional[str] = None, target_module: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a structured 5-day learning path using Graphify's community detection and dependencies.
        """
        if not self.adapter.G:
            return {"error": "Graph is not loaded. Run analyze_repository first."}

        # 1. Gather all files and communities
        communities = self.adapter.get_communities()
        project_summary = self.adapter.get_project_summary()
        key_components = self.adapter.get_key_components()

        # 2. Build a community dependency graph
        # Community A depends on Community B if nodes in A import/call nodes in B
        comm_graph = nx.DiGraph()
        
        # Initialize nodes in community graph
        for cid in communities:
            comm_graph.add_node(cid)

        # Map each code node to its community ID
        node_to_comm = {}
        for cid, comm_data in communities.items():
            for node in comm_data["nodes"]:
                node_to_comm[node["id"]] = cid

        # Find edges between communities
        for u, v in self.adapter.G.edges():
            comm_u = node_to_comm.get(u)
            comm_v = node_to_comm.get(v)
            if comm_u and comm_v and comm_u != comm_v:
                # Add or update edge weight representing coupling strength
                if comm_graph.has_edge(comm_u, comm_v):
                    comm_graph[comm_u][comm_v]["weight"] += 1
                else:
                    comm_graph.add_edge(comm_u, comm_v, weight=1)

        # 3. Sort communities topologically to establish study order
        # Foundational communities (those with more incoming edges in terms of dependency, i.e., other things depend on them)
        # should be studied first.
        # Since standard topological sort works on DAGs, let's find a simple ordering by in-degree / out-degree ratio,
        # or a cycle-breaking topological sort.
        try:
            # Try standard topological sort on DAG if no cycles
            order = list(nx.topological_sort(comm_graph))
            # Reverse order because if A imports B, B is foundational, B should come first
            order.reverse()
        except nx.NetworkXUnfeasible:
            # If there are cycles, order by out-degree minus in-degree (high out-degree depends on others, so learn later)
            scores = {}
            for node in comm_graph.nodes():
                in_deg = comm_graph.in_degree(node, weight="weight")
                out_deg = comm_graph.out_degree(node, weight="weight")
                # Foundational: low out_deg (doesn't import others), high in_deg (others import it)
                scores[node] = out_deg - in_deg
            order = sorted(scores.keys(), key=lambda k: scores[k])

        # Group ordered communities into Day 2, Day 3, Day 4
        # Day 1 is repository setup and overview.
        # Day 5 is tests, deployment, and first contribution.
        study_communities = [communities[cid] for cid in order if cid in communities]

        day2_items = []
        day3_items = []
        day4_items = []

        if len(study_communities) == 1:
            day2_items = study_communities
        elif len(study_communities) == 2:
            day2_items = [study_communities[0]]
            day3_items = [study_communities[1]]
        else:
            # Split approximately evenly
            n = len(study_communities)
            day2_items = study_communities[:max(1, n // 3)]
            day3_items = study_communities[max(1, n // 3):max(2, (2 * n) // 3)]
            day4_items = study_communities[max(2, (2 * n) // 3):]

        # 4. Tailor based on role / target_module
        tailoring_notes = []
        if target_module:
            tailoring_notes.append(f"Focusing roadmap on target module: **{target_module}** and its dependencies.")
            # Promote the target module or its containing community to Day 3 or Day 4,
            # and its dependencies to Day 2.
            # Let's find which community contains target_module
            target_comm_id = None
            for cid, comm_data in communities.items():
                for node in comm_data["nodes"]:
                    if node.get("label") == target_module or node.get("id") == target_module:
                        target_comm_id = cid
                        break
                if target_comm_id:
                    break

            if target_comm_id:
                # Find all communities that this target community depends on
                deps_comm = list(comm_graph.successors(target_comm_id))
                
                # Re-arrange:
                # Day 2: Foundational dependencies of target community
                # Day 3: The Target Community itself (containing target_module)
                # Day 4: High-level modules and integration points
                new_day2 = [communities[cid] for cid in deps_comm if cid in communities]
                new_day3 = [communities[target_comm_id]]
                
                # Day 4 is everything else
                new_day4 = [comm for cid, comm in communities.items() if cid != target_comm_id and cid not in deps_comm]
                
                day2_items = new_day2 if new_day2 else day2_items
                day3_items = new_day3
                day4_items = new_day4 if new_day4 else day4_items

        if role:
            tailoring_notes.append(f"Tailored for role: **{role}**.")

        # 5. Build structured daily instructions
        plan = {
            "title": f"Onboarding Roadmap: {self.adapter.repo_path.name}",
            "role": role,
            "team": team,
            "target_module": target_module,
            "tailoring_notes": tailoring_notes,
            "days": [
                {
                    "day": 1,
                    "theme": "Repository Setup & Overview",
                    "objectives": [
                        "Clone codebase and set up the local development environment.",
                        "Inspect file structure and configure workspace tools.",
                        "Understand key technologies and run the project locally."
                    ],
                    "details": f"Project is a {project_summary.get('architecture_type', 'Application')} using {', '.join(project_summary.get('detected_technologies', []))}.\nVerify configuration files: {', '.join(project_summary.get('config_files', [])) if self.adapter.get_project_summary().get('config_files') else 'None'}."
                },
                {
                    "day": 2,
                    "theme": "Foundational Layers & Utilities",
                    "objectives": [
                        "Examine core utilities, configuration scripts, and baseline library integrations.",
                        "Understand data schemas and shared models."
                    ],
                    "details": self._format_community_list(day2_items)
                },
                {
                    "day": 3,
                    "theme": "Core Business Logic & State Management",
                    "objectives": [
                        "Study the main logical components and algorithmic modules.",
                        "Map key classes, structures, and business rules."
                    ],
                    "details": self._format_community_list(day3_items)
                },
                {
                    "day": 4,
                    "theme": "Controllers, Routing, & Entry Points",
                    "objectives": [
                        "Trace request lifecycle from API/CLI entry points down to core handlers.",
                        "Verify input validations, routers, and request pipeline hooks."
                    ],
                    "details": self._format_community_list(day4_items)
                },
                {
                    "day": 5,
                    "theme": "Verification & First Contribution",
                    "objectives": [
                        "Run the automated test suite and check code coverage.",
                        "Locate simple backlog items, write unit tests, and submit a pull request."
                    ],
                    "details": "Suggested target: Locate code modules, inspect test files, and run the developer build pipeline."
                }
            ],
            "learning_recommendations": {
                "critical_modules": [k["label"] for k in key_components[:3]],
                "files_to_read_first": [n.get("source_file") for n in self.adapter.graph_data.get("nodes", []) if n.get("file_type") == "file"][:5]
            }
        }
        return plan

    def _format_community_list(self, comms: List[Dict[str, Any]]) -> str:
        if not comms:
            return "Explore overall module structure."
        lines = []
        for c in comms:
            lbl = c["label"]
            nodes_labels = [n.get("label") for n in c["nodes"] if n.get("file_type") != "file"][:8]
            files = list(set([n.get("source_file") for n in c["nodes"] if n.get("source_file")]))[:3]
            
            lines.append(f"- **{lbl}**:")
            if nodes_labels:
                lines.append(f"  * Core Components: {', '.join(nodes_labels)}")
            if files:
                lines.append(f"  * Key Files: {', '.join(files)}")
        return "\n".join(lines)
