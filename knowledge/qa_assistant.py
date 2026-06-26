import re
from typing import Dict, Any, List, Optional
from knowledge.graphify_adapter import GraphifyAdapter

class QAAssistant:
    def __init__(self, adapter: GraphifyAdapter):
        self.adapter = adapter

    def explain_module(self, module_name: str) -> Dict[str, Any]:
        """
        Explain a specific module (class, file, or symbol).
        Outputs: Purpose, Responsibilities, Important methods, Dependencies, Related modules.
        """
        if not self.adapter.G:
            return {"error": "Graph not loaded."}

        target_node = None
        target_id = None
        
        # 1. Search for matching node by label (case-insensitive)
        for nid, d in self.adapter.G.nodes(data=True):
            lbl = d.get("label", "")
            if lbl.lower() == module_name.lower() or nid.lower() == module_name.lower():
                target_node = d
                target_id = nid
                break
                
        # If not found by exact match, try partial match
        if not target_node:
            for nid, d in self.adapter.G.nodes(data=True):
                lbl = d.get("label", "")
                if module_name.lower() in lbl.lower() or module_name.lower() in nid.lower():
                    target_node = d
                    target_id = nid
                    break

        if not target_node:
            # Maybe it's a directory module
            modules = self.adapter.get_modules()
            if module_name in modules:
                items = modules[module_name]
                item_labels = [i["label"] for i in items if i["type"] != "file"]
                return {
                    "module_name": module_name,
                    "type": "directory_module",
                    "purpose": f"This is a directory/package module containing {len(items)} files/symbols.",
                    "responsibilities": f"Groups logic for {module_name}.",
                    "important_methods_or_classes": item_labels[:8],
                    "dependencies": [],
                    "related_modules": []
                }
            return {"error": f"Module or component '{module_name}' not found in the codebase intelligence graph."}

        # 2. Extract details from node
        label = target_node.get("label", target_id)
        entity_type = target_node.get("file_type", target_node.get("type", "unknown"))
        desc = target_node.get("description", "No detailed description available.")
        source_file = target_node.get("source_file", "")
        
        # 3. Find dependencies (outgoing edges)
        dependencies = []
        for _, v, ed in self.adapter.G.out_edges(target_id, data=True):
            relation = ed.get("relation", "")
            target_lbl = self.adapter.G.nodes[v].get("label", v) if v in self.adapter.G.nodes else v
            dependencies.append(f"{target_lbl} ({relation})")

        # 4. Find related modules / reverse dependencies (incoming edges)
        related = []
        for u, _, ed in self.adapter.G.in_edges(target_id, data=True):
            relation = ed.get("relation", "")
            source_lbl = self.adapter.G.nodes[u].get("label", u) if u in self.adapter.G.nodes else u
            related.append(f"{source_lbl} ({relation})")

        # 5. Find important methods/contents of classes or files
        methods = []
        if entity_type == "class":
            for successor in self.adapter.G.successors(target_id):
                succ_data = self.adapter.G.nodes[successor]
                if succ_data.get("file_type") in ["method", "class_method", "static_method"]:
                    methods.append(succ_data.get("label"))
        elif entity_type == "file":
            for nid, d in self.adapter.G.nodes(data=True):
                if d.get("source_file") == source_file and d.get("file_type") in ["class", "function"]:
                    methods.append(f"{d.get('label')} ({d.get('file_type')})")

        return {
            "module_name": label,
            "type": entity_type,
            "source_file": source_file,
            "purpose": desc,
            "responsibilities": f"Responsible for executing {entity_type} level behavior in {source_file}.",
            "important_methods": methods,
            "dependencies": list(set(dependencies))[:10],
            "related_modules": list(set(related))[:10]
        }

    def answer_question(self, question: str, work_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Structured Q&A answering questions using graph traversal and tailoring based on work context.
        """
        if not self.adapter.G:
            return {"error": "Graph is not loaded."}

        question_lower = question.lower()
        summary = self.adapter.get_project_summary()
        
        response = {
            "question": question,
            "work_context": work_context,
            "answer_type": "general",
            "structured_answer": ""
        }

        # 1. "How does this project work?" / "request flow" / "architecture"
        if any(q in question_lower for q in ["how does this project work", "architecture", "request flow", "workflow"]):
            response["answer_type"] = "architecture"
            key_components = [k["label"] for k in self.adapter.get_key_components()[:4]]
            
            answer = (
                f"### Project Workflow and Architecture\n\n"
                f"This project is a **{summary.get('architecture_type')}** built using "
                f"**{', '.join(summary.get('detected_technologies', []))}**.\n\n"
                f"#### Core Execution Pipeline:\n"
                f"1. **Entry Points**: Look at `main.py` or configuration/launcher scripts.\n"
                f"2. **Core Processors**: Main business logic is orchestrated by: {', '.join(key_components)}.\n"
                f"3. **Data Flow**: Modules are connected via direct imports and method invocations mapped in the graph.\n\n"
                f"Check the `get_architecture` tool to visualize the exact call-flow graph and dependencies."
            )
            response["structured_answer"] = answer

        # 2. "What are the main modules?" / "list modules"
        elif any(q in question_lower for q in ["main modules", "what are the modules", "list of modules"]):
            response["answer_type"] = "modules"
            modules = self.adapter.get_modules()
            comm_list = []
            for cid, data in self.adapter.get_communities().items():
                comm_list.append(f"- **{data['label']}**: {len(data['nodes'])} components (cohesion: {data['cohesion']:.2f})")
                
            dir_list = [f"- `/{name}/` ({len(items)} files)" for name, items in modules.items()]
            
            answer = (
                f"### Core Codebase Modules\n\n"
                f"The repository is organized into the following directories:\n"
                f"{chr(10).join(dir_list)}\n\n"
                f"Graphify grouped these files into communities/logical domains:\n"
                f"{chr(10).join(comm_list)}"
            )
            response["structured_answer"] = answer

        # 3. "Which component is most important?" / "critical component" / "god node"
        elif any(q in question_lower for q in ["most important", "critical component", "hub", "central"]):
            response["answer_type"] = "importance"
            hubs = self.adapter.get_key_components()[:5]
            hub_lines = []
            for h in hubs:
                desc = h.get("description") or "Core system abstraction."
                hub_lines.append(f"- **{h['label']}** (Degree: {h['degree']}) in file `{h['source_file']}`\n  * *Role*: {desc}")
                
            answer = (
                f"### Central / Critical Components\n\n"
                f"Based on connectivity degree in the codebase dependency graph, the most central components are:\n\n"
                f"{chr(10).join(hub_lines)}"
            )
            response["structured_answer"] = answer

        # 4. "How are modules connected?" / "connections"
        elif any(q in question_lower for q in ["connected", "connections", "how are they connected"]):
            response["answer_type"] = "connectivity"
            deps = self.adapter.get_dependencies()
            internal_sample = []
            for edge in deps["internal"][:6]:
                internal_sample.append(f"- `{edge['source_label']}` calls/imports `{edge['target_label']}` (defined in `{edge['source_file']}`)")
                
            answer = (
                f"### Module Connectivity & Coupling\n\n"
                f"The codebase uses direct imports and function calls. Here is a sample of how components interface:\n\n"
                f"{chr(10).join(internal_sample)}\n\n"
                f"Use `get_dependencies` or `get_architecture` to retrieve the complete dependency graph."
            )
            response["structured_answer"] = answer

        # 5. Check if it's a specific module explanation request inside Q&A
        else:
            words = re.findall(r'[A-Za-z0-9_]+', question)
            matched_explanation = None
            for word in words:
                if len(word) > 4:
                    exp = self.explain_module(word)
                    if "error" not in exp:
                        matched_explanation = exp
                        break
                        
            if matched_explanation:
                response["answer_type"] = "module_explanation"
                methods_str = ", ".join(matched_explanation["important_methods"]) if matched_explanation["important_methods"] else "None"
                deps_str = ", ".join(matched_explanation["dependencies"]) if matched_explanation["dependencies"] else "None"
                rel_str = ", ".join(matched_explanation["related_modules"]) if matched_explanation["related_modules"] else "None"
                
                answer = (
                    f"### Module Explanation: **{matched_explanation['module_name']}** ({matched_explanation['type']})\n\n"
                    f"- **File Location**: `{matched_explanation['source_file']}`\n"
                    f"- **Purpose**: {matched_explanation['purpose']}\n"
                    f"- **Responsibilities**: {matched_explanation['responsibilities']}\n"
                    f"- **Important Methods/Entities**: {methods_str}\n"
                    f"- **Dependencies**: {deps_str}\n"
                    f"- **Invoked By / Related**: {rel_str}"
                )
                response["structured_answer"] = answer
            else:
                response["answer_type"] = "search_fallback"
                results = []
                for nid, d in self.adapter.G.nodes(data=True):
                    lbl = d.get("label", "")
                    desc = d.get("description", "")
                    if question_lower in lbl.lower() or question_lower in desc.lower():
                        results.append(f"- **{lbl}** ({d.get('file_type', 'entity')}): `{d.get('source_file', 'unknown')}` - {desc[:100]}")
                        if len(results) >= 8:
                            break
                if results:
                    answer = (
                        f"### Search Results matching your query:\n\n"
                        f"{chr(10).join(results)}"
                    )
                else:
                    answer = (
                        f"### Repository Q&A\n\n"
                        f"I couldn't find a direct answer to '{question}'. Try asking about: \n"
                        f"- 'How does the project work?'\n"
                        f"- 'What are the main modules?'\n"
                        f"- 'Which components are most important?'"
                    )
                response["structured_answer"] = answer

        # 6. Apply Work Context instruction guidelines if provided
        if work_context and "error" not in response["structured_answer"]:
            related_nodes = []
            context_words = re.findall(r'[A-Za-z0-9_]+', work_context.lower())
            
            for nid, d in self.adapter.G.nodes(data=True):
                lbl = d.get("label", "").lower()
                desc = d.get("description", "").lower()
                if any(w in lbl or w in desc for w in context_words if len(w) > 3):
                    sf = d.get("source_file", "")
                    if sf and sf not in [rn["file"] for rn in related_nodes]:
                        related_nodes.append({"label": d.get("label"), "file": sf, "desc": d.get("description", "")})
                    if len(related_nodes) >= 3:
                        break

            context_instructions = f"\n\n---\n\n### 🎯 Instructions for your task: \"{work_context}\"\n"
            if related_nodes:
                context_instructions += (
                    f"Based on your task, you will likely be working on or around these components:\n"
                )
                for rn in related_nodes:
                    context_instructions += f"- **{rn['label']}** in file `{rn['file']}`\n  * *Context*: {rn['desc'][:120]}...\n"
                context_instructions += (
                    f"\n**Next steps for you**:\n"
                    f"1. Open the files listed above and inspect their local methods.\n"
                    f"2. Check how these files are connected (use `get_architecture` filtering on these components).\n"
                    f"3. Run target tests associated with these modules."
                )
            else:
                context_instructions += (
                    "To start working on this task, review the `list_modules` directory layout to identify "
                    "the components that match your domain, and review our foundational day-by-day learning plan."
                )
            response["structured_answer"] += context_instructions

        return response
