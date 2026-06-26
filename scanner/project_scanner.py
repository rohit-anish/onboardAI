import os
from pathlib import Path
from typing import Dict, Any, List

class ProjectScanner:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def scan(self) -> Dict[str, Any]:
        """
        Scan repository structure, count files, list folders and files.
        """
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {self.repo_path}")

        file_counts = {}
        structure = []
        total_files = 0
        total_size = 0
        
        # Max depth for structure mapping
        max_depth = 3
        
        for root, dirs, files in os.walk(self.repo_path):
            # Exclude common noise dirs
            ignored_dirs = {
                '.git', 'node_modules', '__pycache__', 'venv', '.venv', 
                'dist', 'build', 'graphify-out', '.gemini', '.idea', '.vscode'
            }
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
            
            rel_path = Path(root).relative_to(self.repo_path)
            depth = len(rel_path.parts)
            
            # Map directory structure
            if depth <= max_depth:
                indent = "  " * depth
                folder_name = rel_path.name if rel_path.name else self.repo_path.name
                if rel_path.name:
                    structure.append(f"{indent}📁 {folder_name}/")
                else:
                    structure.append(f"📁 {folder_name}/")
                    
                # Include files up to depth 2
                if depth < max_depth:
                    for f in files:
                        if not f.startswith('.'):
                            structure.append(f"{indent}  📄 {f}")
                            
            for f in files:
                f_path = Path(root) / f
                if any(ignored in f_path.parts for ignored in ignored_dirs) or f.startswith('.'):
                    continue
                total_files += 1
                try:
                    total_size += f_path.stat().st_size
                except Exception:
                    pass
                ext = f_path.suffix.lower()
                if ext:
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                else:
                    file_counts['no_extension'] = file_counts.get('no_extension', 0) + 1
                    
        return {
            "project_name": self.repo_path.name,
            "repo_path": str(self.repo_path),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "file_extensions": file_counts,
            "structure_tree": "\n".join(structure[:100]) # Cap structure tree to prevent bloating outputs
        }
