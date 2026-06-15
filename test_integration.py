import sys
import os
from pathlib import Path

# Ensure absolute import path
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.graphify_adapter import GraphifyAdapter
from knowledge.onboarding_plan import OnboardingPlanGenerator
from knowledge.qa_assistant import QAAssistant
from graph.graph_generator import GraphGenerator

def test_integration():
    repo_path = Path(__file__).parent.resolve()
    print(f"Testing OnboardAI on itself: {repo_path}")
    
    # 1. Initialize Adapter
    adapter = GraphifyAdapter(str(repo_path))
    
    # Check if we can load graph. Since we don't have it yet, this will trigger generation!
    print("Loading graph (this should run graphify extract)...")
    success = adapter.load_graph(auto_generate=True)
    if not success:
        print("FAIL: Failed to load/generate graph.")
        sys.exit(1)
        
    print("SUCCESS: Graph loaded successfully!")
    summary = adapter.get_project_summary()
    print(f"Stats: {summary['stats']}")
    
    # 2. Get Project Summary
    print("\n--- Project Summary ---")
    print(summary["summary"])
    
    # 3. Generate Onboarding Plan
    generator = OnboardingPlanGenerator(adapter)
    plan = generator.generate(role="Onboarding AI Intern", target_module="ProjectScanner")
    print("\n--- Onboarding Roadmap ---")
    for day in plan["days"]:
        print(f"Day {day['day']}: {day['theme']}")
        print(f"  Objectives: {day['objectives']}")
        
    # 4. Explain Module
    assistant = QAAssistant(adapter)
    explanation = assistant.explain_module("ProjectScanner")
    print("\n--- Module Explanation: ProjectScanner ---")
    print(f"Purpose: {explanation.get('purpose', 'N/A')}")
    print(f"Dependencies: {explanation.get('dependencies', [])}")
    
    # 5. Q&A
    qa_result = assistant.answer_question("How does this project work?", work_context="Adding a new tool to server")
    print("\n--- Q&A: How does this project work? ---")
    print(qa_result["structured_answer"])
    
    # 6. Graph Generation
    graph_gen = GraphGenerator(adapter)
    mindmap = graph_gen.generate_mindmap()
    print("\n--- Mindmap Diagram ---")
    print(mindmap)
    
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_integration()
