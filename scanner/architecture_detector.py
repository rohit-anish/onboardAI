import os
from pathlib import Path
from typing import Dict, Any, List, Set

class ArchitectureDetector:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def detect(self) -> Dict[str, Any]:
        """
        Scan repository files for files and content patterns indicating specific framework architectures.
        """
        technologies = set()
        major_dependencies = set()
        configs = []

        # 1. Package configuration files
        package_json = self.repo_path / "package.json"
        requirements_txt = self.repo_path / "requirements.txt"
        pyproject_toml = self.repo_path / "pyproject.toml"
        dockerfile = self.repo_path / "Dockerfile"
        docker_compose = self.repo_path / "docker-compose.yml"
        manage_py = self.repo_path / "manage.py"

        # Check Python package dependencies
        if requirements_txt.exists():
            configs.append("requirements.txt")
            technologies.add("Python")
            try:
                content = requirements_txt.read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in content:
                    technologies.add("FastAPI")
                    major_dependencies.add("FastAPI")
                if "django" in content:
                    technologies.add("Django")
                    major_dependencies.add("Django")
                if "flask" in content:
                    technologies.add("Flask")
                    major_dependencies.add("Flask")
                if "sqlalchemy" in content:
                    technologies.add("SQLAlchemy")
                    major_dependencies.add("SQLAlchemy")
                if "pydantic" in content:
                    major_dependencies.add("Pydantic")
                if "pytest" in content:
                    major_dependencies.add("Pytest")
            except Exception:
                pass

        if pyproject_toml.exists():
            configs.append("pyproject.toml")
            technologies.add("Python")
            try:
                content = pyproject_toml.read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in content:
                    technologies.add("FastAPI")
                    major_dependencies.add("FastAPI")
                if "django" in content:
                    technologies.add("Django")
                    major_dependencies.add("Django")
                if "flask" in content:
                    technologies.add("Flask")
                    major_dependencies.add("Flask")
            except Exception:
                pass

        if manage_py.exists():
            technologies.add("Django")
            configs.append("manage.py")

        # Check Node.js/JavaScript package dependencies
        if package_json.exists():
            configs.append("package.json")
            technologies.add("Node.js")
            try:
                content = package_json.read_text(encoding="utf-8", errors="ignore")
                import json
                data = json.loads(content)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "react" in deps:
                    technologies.add("React")
                    major_dependencies.add("React")
                if "next" in deps:
                    technologies.add("Next.js")
                    major_dependencies.add("Next.js")
                if "vue" in deps:
                    technologies.add("Vue.js")
                    major_dependencies.add("Vue.js")
                if "express" in deps:
                    technologies.add("Express")
                    major_dependencies.add("Express")
                if "typescript" in deps:
                    technologies.add("TypeScript")
                    major_dependencies.add("TypeScript")
                else:
                    technologies.add("JavaScript")
                
                for key in deps:
                    if any(lib in key for lib in ["tailwind", "prisma", "sequelize", "axios", "redux", "graphql"]):
                        major_dependencies.add(key)
            except Exception:
                pass

        # Check Docker configs
        if dockerfile.exists():
            technologies.add("Docker")
            configs.append("Dockerfile")
        if docker_compose.exists() or (self.repo_path / "docker-compose.yaml").exists():
            technologies.add("Docker Compose")
            configs.append("docker-compose.yml")

        # Examine files by extension
        has_js = False
        has_ts = False
        has_py = False
        has_html = False
        has_css = False
        has_rs = False
        has_go = False
        has_java = False

        for root, dirs, files in os.walk(self.repo_path):
            ignored_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build', 'graphify-out'}
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
            for f in files:
                ext = Path(f).suffix.lower()
                if ext == '.py':
                    has_py = True
                elif ext in ['.js', '.jsx']:
                    has_js = True
                elif ext in ['.ts', '.tsx']:
                    has_ts = True
                elif ext == '.html':
                    has_html = True
                elif ext == '.css':
                    has_css = True
                elif ext == '.rs':
                    has_rs = True
                elif ext == '.go':
                    has_go = True
                elif ext == '.java':
                    has_java = True

        if has_py:
            technologies.add("Python")
        if has_js:
            technologies.add("JavaScript")
        if has_ts:
            technologies.add("TypeScript")
        if has_html:
            technologies.add("HTML")
        if has_css:
            technologies.add("CSS")
        if has_rs:
            technologies.add("Rust")
        if has_go:
            technologies.add("Go")
        if has_java:
            technologies.add("Java")

        return {
            "detected_technologies": list(sorted(technologies)),
            "major_dependencies": list(sorted(major_dependencies)),
            "config_files": configs,
            "architecture_type": self._determine_architecture_type(technologies)
        }

    def _determine_architecture_type(self, technologies: Set[str]) -> str:
        if "React" in technologies or "Next.js" in technologies:
            if "FastAPI" in technologies or "Django" in technologies:
                return "Full Stack (React + Python Backend)"
            if "Express" in technologies or "Node.js" in technologies:
                return "Full Stack (React + Node.js Backend)"
            return "Frontend Application (React/Web)"
        if "FastAPI" in technologies:
            return "FastAPI API Backend"
        if "Django" in technologies:
            return "Django Full-Stack / API"
        if "Python" in technologies:
            return "Python Codebase"
        if "Node.js" in technologies:
            return "Node.js Application"
        return "Generic Application / Polyglot"
