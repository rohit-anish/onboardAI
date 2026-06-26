from pathlib import Path


class ArchitectureDetector:
    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def detect(self):
        architecture = {
            "frontend": None,
            "backend": None,
            "database": None,
            "deployment": None
        }

        requirements_file = self.project_path / "requirements.txt"

        if requirements_file.exists():
            content = requirements_file.read_text(
                errors="ignore"
            ).lower()

            if "fastapi" in content:
                architecture["backend"] = "FastAPI"

            if "django" in content:
                architecture["backend"] = "Django"

        package_json = self.project_path / "package.json"

        if package_json.exists():
            content = package_json.read_text(
                errors="ignore"
            ).lower()

            if "react" in content:
                architecture["frontend"] = "React"

            if "next" in content:
                architecture["frontend"] = "Next.js"

        docker_file = self.project_path / "dockerfile"

        if docker_file.exists():
            architecture["deployment"] = "Docker"

        return architecture