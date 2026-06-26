from pathlib import Path


class ProjectScanner:
    IGNORED_DIRS = {
        ".venv",
        "__pycache__",
        ".git",
        "node_modules",
        ".idea",
        ".vscode"
    }

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def detect_technologies(self):
        technologies = set()

        if (self.project_path / "requirements.txt").exists():
            technologies.add("Python")

            content = (
                self.project_path / "requirements.txt"
            ).read_text(errors="ignore").lower()

            if "fastapi" in content:
                technologies.add("FastAPI")

            if "django" in content:
                technologies.add("Django")

        if (self.project_path / "package.json").exists():
            technologies.add("Node.js")

            content = (
                self.project_path / "package.json"
            ).read_text(errors="ignore").lower()

            if "react" in content:
                technologies.add("React")

            if "next" in content:
                technologies.add("Next.js")

        return sorted(list(technologies))

    def scan(self):
        file_count = 0

        for item in self.project_path.rglob("*"):
            if any(part in self.IGNORED_DIRS for part in item.parts):
                continue

            if item.is_file():
                file_count += 1

        return {
            "project_name": self.project_path.name,
            "total_files": file_count,
            "detected_technologies": self.detect_technologies()
        }