class GraphGenerator:
    def __init__(self, architecture):
        self.architecture = architecture

    def generate_mermaid(self):
        frontend = self.architecture.get("frontend")
        backend = self.architecture.get("backend")
        database = self.architecture.get("database")

        graph = ["graph TD"]

        if frontend and backend:
            graph.append(f"{frontend} --> {backend}")

        if backend and database:
            graph.append(f"{backend} --> {database}")

        if backend and not frontend:
            graph.append(f"Project --> {backend}")

        return "\n".join(graph)