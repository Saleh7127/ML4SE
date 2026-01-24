"""
Clone every repository listed in repos_dataset.jsonl.

Usage:
    python repo_cloner.py \
        --dataset repos_dataset.jsonl \
        --dest downloaded_repos \
        --workers 4

The script expects a JSONL file where each line contains at least a
`full_name` (owner/repo) or `url` field, plus an optional `default_branch`.
Existing directories are skipped unless --force is provided.
"""

import argparse
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download repositories from a JSONL dataset.")
    parser.add_argument("--dataset", default="data/repos_dataset.jsonl", help="Path to JSONL dataset.")
    parser.add_argument("--dest", default="data/repositories", help="Destination directory for clones.")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent clone workers.")
    parser.add_argument("--force", action="store_true", help="Re-clone repositories even if already present.")
    parser.add_argument("--limit", type=int, default=None, help="Limit how many repos to clone.")
    return parser.parse_args()


def read_dataset(path: Path, limit: Optional[int] = None) -> List[Dict]:
    repos: List[Dict] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping malformed line {idx} in {path}")
                continue
            repos.append(data)
            if limit is not None and len(repos) >= limit:
                break
    return repos


def build_clone_url(full_name: Optional[str], url: Optional[str]) -> Optional[str]:
    if full_name:
        return f"https://github.com/{full_name}.git"
    if url:
        if url.endswith(".git") or url.startswith("git@"):
            return url
        if url.startswith("http"):
            return url.rstrip("/") + ".git"
    return None


def repo_dirname(full_name: Optional[str], url: Optional[str]) -> str:
    ident = full_name or url or "unknown_repo"
    return ident.replace("/", "__")


def clone_repo(entry: Dict, dest_root: Path, force: bool = False) -> Tuple[str, str]:
    repo_url = build_clone_url(entry.get("full_name"), entry.get("url"))
    repo_name = entry.get("full_name") or entry.get("url") or "unknown"
    branch = entry.get("default_branch") or "main"
    target = dest_root / repo_dirname(entry.get("full_name"), entry.get("url"))

    if target.exists():
        if force:
            shutil.rmtree(target)
        else:
            return repo_name, "skipped (already exists)"

    if not repo_url:
        return repo_name, "error: missing repository URL"

    cmd = ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(target)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or f"clone failed ({result.returncode})"
        return repo_name, f"error: {msg}"
    return repo_name, "ok"


def clone_all(repos: Iterable[Dict], dest_root: Path, workers: int, force: bool) -> None:
    dest_root.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(clone_repo, repo, dest_root, force): repo for repo in repos}
        for future in as_completed(future_map):
            repo_name, status = future.result()
            print(f"[{status}] {repo_name}")


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    repos = read_dataset(dataset_path, limit=args.limit)
    if not repos:
        raise SystemExit("No repositories to clone.")

    print(f"Cloning {len(repos)} repositories into {args.dest} with {args.workers} workers...")
    clone_all(repos, Path(args.dest), workers=args.workers, force=args.force)


if __name__ == "__main__":
    main()
