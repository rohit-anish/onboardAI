import sys
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

from knowledge.graphify_adapter import GraphifyAdapter
from knowledge.onboarding_plan import OnboardingPlanGenerator
from knowledge.repository_inventory import RepositoryInventory
from knowledge.qa_assistant import QAAssistant
from graph.graph_generator import GraphGenerator

# Initialize FastMCP Server
mcp = FastMCP(
    "OnboardAI",
    dependencies=["networkx", "fastapi", "uvicorn", "pydantic", "mcp"]
)

def get_adapter(repo_path: str, auto_generate: bool = True) -> GraphifyAdapter:
    """Helper to initialize and load GraphifyAdapter."""
    adapter = GraphifyAdapter(repo_path)
    adapter.load_graph(auto_generate=auto_generate)
    return adapter

@mcp.tool()
def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    Perform a complete repository scan and architecture detection.
    Triggers Graphify graph extraction if not already present.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    return adapter.get_project_summary()

@mcp.tool()
def generate_onboarding_plan(
    repo_path: str,
    role: Optional[str] = None,
    team: Optional[str] = None,
    target_module: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a 5-day customized learning path / roadmap for the repository.
    Can be tailored based on the developer's role, team, or target module they will work on.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    
    generator = OnboardingPlanGenerator(adapter)
    return generator.generate(role=role, team=team, target_module=target_module)

@mcp.tool()
def explain_project(repo_path: str) -> Dict[str, Any]:
    """
    Provide a high-level architectural overview and summary of the codebase.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    return adapter.get_project_summary()

@mcp.tool()
def explain_module(repo_path: str, module_name: str) -> Dict[str, Any]:
    """
    Provide a detailed explanation of a specific module, class, or file.
    Outputs the purpose, responsibilities, methods, dependencies, and related modules.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    
    assistant = QAAssistant(adapter)
    return assistant.explain_module(module_name)

@mcp.tool()
def list_modules(repo_path: str) -> Dict[str, Any]:
    """
    List all file-level and directory-level modules inside the repository.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    return {"modules": adapter.get_modules()}

@mcp.tool()
def search_repository(repo_path: str, query: str) -> List[Dict[str, Any]]:
    """
    Search classes, functions, and symbols within the repository graph.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return []
    
    query_lower = query.lower()
    results = []
    for nid, d in adapter.G.nodes(data=True):
        lbl = d.get("label", "")
        desc = d.get("description", "")
        if query_lower in lbl.lower() or query_lower in desc.lower() or query_lower in nid.lower():
            results.append({
                "id": nid,
                "label": lbl,
                "type": d.get("file_type", "entity"),
                "file": d.get("source_file", ""),
                "description": desc
            })
    return results[:15]

@mcp.tool()
def get_architecture(repo_path: str, visualization_type: str = "dependency") -> Dict[str, Any]:
    """
    Generate Mermaid-based visualizations of the project architecture.
    visualization_type can be:
    - 'dependency': High-level module dependencies (default)
    - 'callflow': Functional/method call flows
    - 'mindmap': Visual mindmap of project structure
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    
    generator = GraphGenerator(adapter)
    diagram = ""
    
    if visualization_type == "mindmap":
        diagram = generator.generate_mindmap()
    elif visualization_type == "callflow":
        diagram = generator.generate_call_flow()
    else:
        diagram = generator.generate_dependency_graph()
        
    return {
        "visualization_type": visualization_type,
        "mermaid_diagram": diagram
    }

@mcp.tool()
def get_learning_path(repo_path: str) -> Dict[str, Any]:
    """
    Get recommended first read list and critical core modules to study first.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    
    generator = OnboardingPlanGenerator(adapter)
    plan = generator.generate()
    return plan.get("learning_recommendations", {})

@mcp.tool()
def get_dependencies(repo_path: str) -> Dict[str, Any]:
    """
    Retrieve external package dependencies and internal component couplings.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    return adapter.get_dependencies()

@mcp.tool()
def ask_repository_question(
    repo_path: str,
    question: str,
    work_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ask specific questions about codebase architecture, connections, or important concepts.
    If 'work_context' is provided (e.g. details about what features/tasks you are assigned),
    it generates tailored step-by-step instructions for where to focus.
    """
    adapter = get_adapter(repo_path, auto_generate=True)
    if not adapter.G:
        return {"error": "Failed to load or generate repository intelligence graph."}
    
    assistant = QAAssistant(adapter)
    return assistant.answer_question(question, work_context)
