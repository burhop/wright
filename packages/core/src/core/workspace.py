import os
from typing import Dict, Any

class WorkspaceManager:
    """Manages workspace file browser directory tree construction and raw file reads."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)

    def sanitize_path(self, relative_path: str) -> str:
        """Sanitize relative path and resolve to absolute path under base_dir to prevent path traversal."""
        # Clean relative_path of leading/trailing slashes
        clean_rel = relative_path.strip("/")
        # Resolve path
        resolved = os.path.abspath(os.path.join(self.base_dir, clean_rel))
        # Ensure it's under base_dir
        if not resolved.startswith(self.base_dir):
            raise ValueError("Access denied: path traversal attempt detected.")
        return resolved

    def get_workspace_tree(self) -> Dict[str, Any]:
        """Build the complete hierarchical file tree for the base_dir."""
        if not os.path.exists(self.base_dir):
            # Create if it doesn't exist (e.g. initial start)
            os.makedirs(self.base_dir, exist_ok=True)
        return self._build_node(self.base_dir)

    def _build_node(self, abs_path: str) -> Dict[str, Any]:
        name = os.path.basename(abs_path)
        if not name:
            name = os.path.basename(self.base_dir)
        
        # Build clean project-relative slash prefix paths (e.g., /designs/gearbox.stl)
        if abs_path == self.base_dir:
            rel_path = "/"
        else:
            rel_path = "/" + os.path.relpath(abs_path, self.base_dir).strip("/")

        stat = os.stat(abs_path)
        last_modified = int(stat.st_mtime)

        if os.path.isdir(abs_path):
            children = []
            try:
                for entry in sorted(os.listdir(abs_path)):
                    # Skip hidden files
                    if entry.startswith("."):
                        continue
                    child_abs = os.path.join(abs_path, entry)
                    children.append(self._build_node(child_abs))
            except Exception:
                pass
            return {
                "name": name,
                "path": rel_path,
                "type": "directory",
                "size": None,
                "last_modified": last_modified,
                "children": children
            }
        else:
            return {
                "name": name,
                "path": rel_path,
                "type": "file",
                "size": stat.st_size,
                "last_modified": last_modified,
                "children": None
            }

    def read_file_content(self, rel_path: str) -> bytes:
        """Read and return binary content of a file."""
        abs_path = self.sanitize_path(rel_path)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {rel_path}")
        with open(abs_path, "rb") as f:
            return f.read()
