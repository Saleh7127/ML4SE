"""
Delete README files from all repositories under data/repositories.

Usage:
    python scripts/remove_readmes.py \
        --repos-root data/repositories \
        [--filenames README.md README.txt] \
        [--dry-run]

By default this removes files immediately. Use --dry-run to preview what
would be deleted without modifying the filesystem.
"""

import argparse
import os
from pathlib import Path
from typing import List, Set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove README files from repositories.")
    parser.add_argument("--repos-root", default="data/repositories", help="Path containing cloned repositories.")
    parser.add_argument(
        "--filenames",
        nargs="*",
        default=["README.md", "README", "readme.md", "readme"],
        help="README filenames to delete (case-insensitive match).",
    )
    parser.add_argument("--dry-run", action="store_true", help="List files that would be removed without deleting.")
    return parser.parse_args()


def find_readmes(repo_dir: Path, targets: Set[str]) -> List[Path]:
    matches: List[Path] = []
    for root, _, files in os.walk(repo_dir):
        for fname in files:
            if fname.lower() in targets:
                matches.append(Path(root) / fname)
    return matches


def remove_readmes(root: Path, targets: Set[str], dry_run: bool) -> int:
    removed = 0
    for repo_dir in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not repo_dir.is_dir():
            continue
        readmes = find_readmes(repo_dir, targets)
        for path in readmes:
            if dry_run:
                print(f"[DRY-RUN] Would delete {path}")
            else:
                try:
                    path.unlink()
                    print(f"Deleted {path}")
                    removed += 1
                except OSError as exc:
                    print(f"Failed to delete {path}: {exc}")
    return removed


def main() -> None:
    args = parse_args()
    repos_root = Path(args.repos_root)
    if not repos_root.exists():
        raise SystemExit(f"Repos root not found: {repos_root}")
    targets = {name.lower() for name in args.filenames}
    removed = remove_readmes(repos_root, targets, args.dry_run)
    suffix = " (dry-run)" if args.dry_run else ""
    print(f"Total README files {'found' if args.dry_run else 'deleted'}: {removed}{suffix}")


if __name__ == "__main__":
    main()
