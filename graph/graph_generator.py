from typing import Dict, Any, List
from knowledge.graphify_adapter import GraphifyAdapter

class GraphGenerator:
    def __init__(self, adapter: GraphifyAdapter):
        self.adapter = adapter

    def generate_mindmap(self) -> str:
        """
        Generate a Mermaid mindmap representing the repository layout and core component dependencies.
        """
        if not self.adapter.G:
            return "%% Graph not loaded %%"

        proj_name = self.adapter.repo_path.name
        mindmap = [
            "mindmap",
            f"  root(({proj_name}))"
        ]

        # Group by directory
        modules = self.adapter.get_modules()
        for mod_name, items in list(modules.items())[:6]:  # Limit to 6 modules to keep mindmap readable
            mindmap.append(f"    {mod_name}")
            
            # Sub-items: key classes/files
            seen_labels = set()
            added_count = 0
            for item in items:
                lbl = item["label"]
                if lbl not in seen_labels and item["type"] in ["class", "function", "file"]:
                    seen_labels.add(lbl)
                    clean_lbl = lbl.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace(" ", "_")
                    mindmap.append(f"      {clean_lbl}")
                    added_count += 1
                    if added_count >= 4:  # Cap at 4 items per branch
                        break
                        
        return "\n".join(mindmap)

    def generate_call_flow(self) -> str:
        """
        Generate a Mermaid flow diagram showing function calls and method invocations.
        """
        if not self.adapter.G:
            return "%% Graph not loaded %%"
            
        mermaid = [
            "flowchart TD"
        ]
        
        deps = self.adapter.get_dependencies()
        call_edges = [edge for edge in deps["internal"] if edge["relation"] == "calls"]
        
        seen_edges = set()
        node_ids = set()
        for edge in call_edges[:25]:  # Limit to top 25 calls
            u, v = edge["source"], edge["target"]
            u_lbl = edge["source_label"].replace("(", "").replace(")", "")
            v_lbl = edge["target_label"].replace("(", "").replace(")", "")
            
            u_id = u.replace("/", "_").replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
            v_id = v.replace("/", "_").replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
            
            node_ids.add(f"  {u_id}[\"{u_lbl}\"]")
            node_ids.add(f"  {v_id}[\"{v_lbl}\"]")
            
            edge_key = (u_id, v_id)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                mermaid.append(f"  {u_id} -->|calls| {v_id}")
                
        mermaid = [mermaid[0]] + list(node_ids) + mermaid[1:]
        
        return "\n".join(mermaid)

    def generate_dependency_graph(self) -> str:
        """
        Generate a Mermaid flowchart of module-to-module dependencies.
        """
        if not self.adapter.G:
            return "%% Graph not loaded %%"
            
        mermaid = [
            "flowchart LR"
        ]
        
        deps = self.adapter.get_dependencies()
        import_edges = [edge for edge in deps["internal"] if edge["relation"] == "imports"]
        
        seen_edges = set()
        node_ids = set()
        for edge in import_edges[:30]:  # Limit to 30 dependencies
            u, v = edge["source"], edge["target"]
            u_lbl = edge["source_label"].replace("[", "").replace("]", "")
            v_lbl = edge["target_label"].replace("[", "").replace("]", "")
            
            u_id = u.replace("/", "_").replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
            v_id = v.replace("/", "_").replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
            
            node_ids.add(f"  {u_id}[\"{u_lbl}\"]")
            node_ids.add(f"  {v_id}[\"{v_lbl}\"]")
            
            edge_key = (u_id, v_id)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                mermaid.append(f"  {u_id} -.-> {v_id}")
                
        mermaid = [mermaid[0]] + list(node_ids) + mermaid[1:]
        return "\n".join(mermaid)
