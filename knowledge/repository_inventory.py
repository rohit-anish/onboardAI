from typing import Dict, Any, List
from knowledge.graphify_adapter import GraphifyAdapter

class RepositoryInventory:
    def __init__(self, adapter: GraphifyAdapter):
        self.adapter = adapter

    def get_inventory(self) -> Dict[str, Any]:
        """
        Produce a catalog of all modules, classes, and methods/functions.
        """
        if not self.adapter.G:
            return {"error": "Graph not loaded"}

        inventory = {}
        for nid, d in self.adapter.G.nodes(data=True):
            sf = d.get("source_file", "")
            if not sf:
                continue

            entity_type = d.get("file_type", d.get("type", "unknown"))
            if entity_type == "file":
                # Save file level description if it has one
                file_entry = inventory.setdefault(sf, {
                    "file": sf,
                    "classes": {},
                    "functions": [],
                    "description": d.get("description", "")
                })
                continue

            file_entry = inventory.setdefault(sf, {
                "file": sf,
                "classes": {},
                "functions": [],
                "description": ""
            })

            if entity_type == "rationale":
                file_entry["description"] = d.get("label", "")
                continue

            label = d.get("label", nid)
            desc = d.get("description", "")

            if entity_type == "class":
                file_entry["classes"][label] = {
                    "name": label,
                    "description": desc,
                    "methods": []
                }
            elif entity_type == "function":
                file_entry["functions"].append({
                    "name": label,
                    "description": desc
                })
            elif entity_type in ["method", "class_method", "static_method"]:
                # Try to find which class this method belongs to
                class_found = False
                for pred in self.adapter.G.predecessors(nid):
                    pred_data = self.adapter.G.nodes[pred]
                    if pred_data.get("file_type") == "class":
                        class_label = pred_data.get("label")
                        if class_label in file_entry["classes"]:
                            file_entry["classes"][class_label]["methods"].append({
                                "name": label,
                                "description": desc
                            })
                            class_found = True
                            break
                if not class_found:
                    file_entry["functions"].append({
                        "name": label,
                        "description": desc
                    })

        # Format as list of modules
        modules_list = []
        for file_path, data in inventory.items():
            modules_list.append({
                "file": file_path,
                "description": data["description"],
                "classes": list(data["classes"].values()),
                "functions": data["functions"]
            })

        return {"modules": modules_list}
