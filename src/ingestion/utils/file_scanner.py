import os
from pathlib import Path

def generate_file_tree(start_path: str, max_depth: int = 2) -> str:
    """
    Generates a string representation of the file tree structure starting from start_path.
    Respects common ignore patterns.
    """
    start_path = Path(start_path)
    if not start_path.exists():
        return f"Error: Path {start_path} does not exist."

    tree_str = []
    
    # Common ignore patterns
    IGNORE_DIRS = {
        '.git', 'node_modules', '__pycache__', '.idea', '.vscode', 'venv', 'env', 
        'build', 'dist', 'target', '.DS_Store', 'coverage', '.pytest_cache'
    }
    IGNORE_FILES = {
        '.DS_Store', 'package-lock.json', 'yarn.lock', 'poetry.lock', 
        'Cargo.lock', '.gitignore', '.env'
    }

    IGNORE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', 
        '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.pdf', '.zip', '.gz'
    }

    def _tree(dir_path: Path, prefix: str = "", current_depth: int = 0):
        if current_depth > max_depth:
            return

        try:
            items = sorted(os.listdir(dir_path), key=lambda x: (not (dir_path / x).is_dir(), x.lower()))
        except PermissionError:
            return

        filtered_items = []
        for item in items:
            full_path = dir_path / item
            if (item not in IGNORE_DIRS and 
                item not in IGNORE_FILES and 
                not item.startswith('.') and
                full_path.suffix.lower() not in IGNORE_EXTENSIONS):
                filtered_items.append(item)

        entries_count = len(filtered_items)
        
        for i, item in enumerate(filtered_items):
            path = dir_path / item
            is_last = (i == entries_count - 1)
            
            connector = "└── " if is_last else "├── "
            
            if path.is_dir():
                tree_str.append(f"{prefix}{connector}{item}/")
                extension = "    " if is_last else "│   "
                _tree(path, prefix + extension, current_depth + 1)
            else:
                tree_str.append(f"{prefix}{connector}{item}")

    tree_str.append(f"{start_path.name}/")
    _tree(start_path)
    return "\n".join(tree_str)

if __name__ == "__main__":
    # Test run
    print(generate_file_tree("."))
