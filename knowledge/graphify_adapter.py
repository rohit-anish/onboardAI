import json
from pathlib import Path


class GraphifyAdapter:
    def __init__(self, graphify_output_path):
        self.output_path = Path(graphify_output_path)

        with open(
            self.output_path / ".graphify_analysis.json",
            "r",
            encoding="utf-8"
        ) as f:
            self.analysis = json.load(f)

    def get_communities(self):
        return self.analysis.get("communities", {})

    def get_key_components(self):
        return self.analysis.get("gods", [])