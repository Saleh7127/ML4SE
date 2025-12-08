"""
Extract README.md files from repositories and copy them to a separate folder.

Usage:
    python scripts/extract_readmes.py \
        --repos-root data/repository \
        --output-dir data/readmes
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract README.md files from repositories.")
    parser.add_argument("--repos-root", default="data/repository", help="Path containing cloned repositories.")
    parser.add_argument("--output-dir", default="data/readmes", help="Directory where README copies will be saved.")
    parser.add_argument(
        "--filenames",
        nargs="*",
        default=["README.md"],
        help="README filenames to search for (case-insensitive).",
    )
    return parser.parse_args()


def find_readme(repo_dir: Path, filenames: List[str]) -> Optional[Path]:
    candidates: List[Path] = []
    wanted = {name.lower() for name in filenames}
    for path in repo_dir.rglob("*"):
        if path.is_file() and path.name.lower() in wanted:
            candidates.append(path)
    if not candidates:
        return None
    # Prefer the most top-level README (shortest relative path), then alphabetical
    candidates.sort(key=lambda p: (len(p.relative_to(repo_dir).parts), str(p).lower()))
    return candidates[0]


def copy_readmes(root: Path, out_dir: Path, filenames: List[str]) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for repo_dir in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not repo_dir.is_dir():
            continue
        readme_path = find_readme(repo_dir, filenames)
        if not readme_path:
            continue
        dest_name = f"{repo_dir.name}.md"
        dest_path = out_dir / dest_name
        shutil.copy(readme_path, dest_path)
        count += 1
    return count


def main() -> None:
    args = parse_args()
    repos_root = Path(args.repos_root)
    output_dir = Path(args.output_dir)
    if not repos_root.exists():
        raise SystemExit(f"Repos root not found: {repos_root}")
    copied = copy_readmes(repos_root, output_dir, args.filenames)
    print(f"Copied {copied} README files to {output_dir}")


if __name__ == "__main__":
    main()
