from pathlib import Path


class RepositoryInventory:
    IGNORED_DIRS = {
        ".venv",
        "__pycache__",
        ".git",
        "node_modules"
    }

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def generate(self):
        folders = []

        for item in self.project_path.iterdir():
            if item.is_dir():
                if item.name not in self.IGNORED_DIRS:
                    folders.append(item.name)

        return sorted(folders)