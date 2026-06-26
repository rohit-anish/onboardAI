from scanner.project_scanner import ProjectScanner
from scanner.architecture_detector import ArchitectureDetector
from graph.graph_generator import GraphGenerator
from knowledge.repository_inventory import RepositoryInventory

from knowledge.graphify_adapter import GraphifyAdapter

adapter = GraphifyAdapter(
    "graphify-out"
)

print(adapter.get_communities())
print(adapter.get_key_components())

project_path = input("Enter project path: ")

scanner = ProjectScanner(project_path)
scan_result = scanner.scan()

detector = ArchitectureDetector(project_path)
architecture = detector.detect()

graph_generator = GraphGenerator(architecture)
mermaid_graph = graph_generator.generate_mermaid()

inventory = RepositoryInventory(project_path)
folders = inventory.generate()

print("\nSCAN RESULT")
print(scan_result)

print("\nARCHITECTURE")
print(architecture)

print("\nMERMAID GRAPH")
print(mermaid_graph)

print("\nPROJECT MODULES")

for folder in folders:
    print(f"- {folder}")