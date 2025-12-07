"""
Harvest small, real GitHub projects with good READMEs and snapshot them
into a JSONL dataset for a README-generation MAS.

Stages:
    A) GraphQL-based candidate harvester
    B) README scorer + reranker
    C) Snapshotter → repos_dataset.jsonl

Usage:
    export GITHUB_TOKEN="ghp_xxx"
    python repo_finder.py
"""

import os
import sys
import time
import json
import base64
import re
from typing import Dict, Any, List, Optional

import requests



GITHUB_TOKEN = "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"
if not GITHUB_TOKEN:
    print("ERROR: Please set GITHUB_TOKEN env var first (export GITHUB_TOKEN=...).")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL_BASE = "https://api.github.com"

PER_LANG_TARGET = 20

MAX_FILES_PER_REPO = 20
MAX_FILE_BYTES = 1000
MIN_README_CHARS = 1000

DATASET_PATH = "data/repos_dataset.jsonl"

LANGUAGES = ["Python", "JavaScript"]

TARGET_REPOS = PER_LANG_TARGET * len(LANGUAGES)

README_KEYWORDS = [
    '"installation" "usage"',
    '"features"',
    '"overview" OR "introduction"',
    '"getting started"',
    '"quick start" OR "quickstart"',
    '"examples"',
    '"how to run"',
    '"docker run" OR "docker compose"',
    '"pip install" OR "npm install"',
]

BASE_QUERY = (
    "stars:10..100 "
    "size:100..1000 "
    "pushed:>=2023-01-01 "
    "fork:false archived:false has:readme "
)

NEGATIVE_FILTERS = (
    "-in:name awesome -in:description awesome "
    "-topic:awesome -topic:interview -topic:collection -topic:awesome-list -topic:cheat-sheet"      
    "-topic:tutorial -topic:guide -topic:documentation"
    "-topic:starter -topic:template -topic:example -topic:demo -topic:tool"
)

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".cpp", ".c", ".h", ".rb", ".php", ".swift", ".kt", ".lua", ".sh", ".ipynb"
}


SECTION_PAT = re.compile(
    r"(?im)^\s*#{1,3}\s*("
    r"installation|usage|setup|getting\s*started|quick\s*start|"
    r"features|overview|introduction|examples|"
    r"contributing|license"
    r")\b"
)


def score_readme(
    text: Optional[str],
    byte_size: int,
    disk_kb: int,
    stars: int
) -> float:
    """
    Heuristic README quality score in [0,1].
    Higher is better.
    """
    if not text:
        return 0.0

    length_ok = 1.0 if len(text) >= MIN_README_CHARS else 0.0
    sections = len(SECTION_PAT.findall(text))
    section_cov = min(sections / 4.0, 1.0)

    code_blocks = text.count("```")
    code_norm = min(code_blocks / 3.0, 1.0)

    links = 1.0 if "http" in text or "https" in text else 0.0
    size_ok = 1.0 if 100 <= disk_kb <= 5000 else 0.0
    stars_norm = min(stars / 1000.0, 1.0)

    score = (
        0.35 * length_ok +
        0.25 * section_cov +
        0.15 * code_norm +
        0.10 * links +
        0.10 * size_ok +
        0.05 * stars_norm
    )
    return round(score, 3)


def handle_rate_limit(resp: requests.Response):
    """Sleep until rate limit resets if necessary."""
    if resp.status_code == 403:
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset:
            reset_ts = int(reset)
            now = int(time.time())
            wait = max(reset_ts - now, 5)
            print(f"Rate limit hit. Sleeping {wait} seconds...")
            time.sleep(wait)
        else:
            print("Rate limit 403, but no reset header. Sleeping 60 seconds...")
            time.sleep(60)


def graphql(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        resp = requests.post(
            GRAPHQL_URL,
            headers=HEADERS,
            json={"query": query, "variables": variables},
        )
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                print("GraphQL errors:", data["errors"])
            return data
        else:
            print(f"GraphQL error: {resp.status_code}, {resp.text[:200]}")
            handle_rate_limit(resp)


def rest_get(path: str, params: Dict[str, Any] = None) -> Optional[requests.Response]:
    url = f"{REST_URL_BASE}{path}"
    while True:
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 404:
            return None
        else:
            print(f"REST error {resp.status_code} on {url}: {resp.text[:200]}")
            handle_rate_limit(resp)


SEARCH_REPOS_QUERY = """
query($query: String!, $after: String) {
  search(type: REPOSITORY, query: $query, first: 20, after: $after) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on Repository {
          nameWithOwner
          url
          stargazerCount
          isFork
          isArchived
          diskUsage
          primaryLanguage { name }
          defaultBranchRef { name }
          readme: object(expression: "HEAD:README.md") {
            ... on Blob {
              text
              byteSize
            }
          }
        }
      }
    }
  }
}
"""


def gen_search_queries(langs: Optional[List[str]] = None) -> List[str]:
    """Generate search queries. If `langs` is provided, only generate for those languages."""
    if langs is None:
        langs = LANGUAGES
    queries = []
    for lang in langs:
        for kw in README_KEYWORDS:
            q = f'{BASE_QUERY} language:{lang} in:readme {kw} {NEGATIVE_FILTERS}'
            queries.append(q)
    return queries


def harvest_candidates(max_repos: int, languages: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Harvest candidates for the provided `languages` (or all LANGUAGES if None)."""
    queries = gen_search_queries(languages)
    seen = set()
    candidates: List[Dict[str, Any]] = []

    print(f"Generated {len(queries)} search queries.")
    print(f"Target final repos: {max_repos}\n")

    for q_idx, query in enumerate(queries):
        if len(candidates) >= max_repos * 3:
            break

        print(f"[{q_idx + 1}/{len(queries)}] Query: {query}")
        after = None

        while True:
            data = graphql(SEARCH_REPOS_QUERY, {"query": query, "after": after})
            search = data.get("data", {}).get("search", {})
            edges = search.get("edges", [])
            page_info = search.get("pageInfo", {})
            if not edges:
                break

            for edge in edges:
                node = edge["node"]
                full_name = node["nameWithOwner"]
                if full_name in seen:
                    continue
                seen.add(full_name)

                if node["isFork"] or node["isArchived"]:
                    continue

                readme = node.get("readme")
                readme_text = readme.get("text") if readme else None
                readme_bytes = readme.get("byteSize") if readme else 0

                repo = {
                    "full_name": full_name,
                    "url": node["url"],
                    "stars": node["stargazerCount"],
                    "disk_kb": node["diskUsage"] or 0,
                    "primary_language": (node["primaryLanguage"] or {}).get("name"),
                    "default_branch": (node["defaultBranchRef"] or {}).get("name"),
                    "readme_text": readme_text,
                    "readme_bytes": readme_bytes,
                }

                candidates.append(repo)

                if len(candidates) % 20 == 0:
                    print(f"   + Collected candidates: {len(candidates)}")

                if len(candidates) >= max_repos * 3:
                    break

            if len(candidates) >= max_repos * 3:
                break

            if not page_info.get("hasNextPage"):
                break
            after = page_info.get("endCursor")

        print(f"  Done query. Total candidates so far: {len(candidates)}\n")

    print(f" Harvest complete. Raw candidate count: {len(candidates)}")
    return candidates


def filter_and_score(candidates: List[Dict[str, Any]], target: int, min_score: float = 0.6) -> List[Dict[str, Any]]:
    scored = []
    for repo in candidates:
        score = score_readme(
            repo.get("readme_text"),
            repo.get("readme_bytes") or 0,
            repo.get("disk_kb") or 0,
            repo.get("stars") or 0,
        )
        repo["readme_score"] = score
        scored.append(repo)

    scored.sort(key=lambda r: r["readme_score"], reverse=True)

    filtered = [r for r in scored if r["readme_score"] >= min_score]

    print(f" Scored {len(candidates)} repos.")
    print(f"   Kept {len(filtered)} with README score >= {min_score}\n")

    return filtered[:target]


def is_code_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in CODE_EXTENSIONS


def snapshot_repo(repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    full_name = repo["full_name"]
    owner, name = full_name.split("/")
    branch = repo["default_branch"] or "HEAD"

    print(f"  Snapshotting {full_name} (branch: {branch})")

    tree_resp = rest_get(f"/repos/{owner}/{name}/git/trees/{branch}", params={"recursive": "1"})
    if tree_resp is None:
        print(f"  Tree not found for {full_name}")
        return None

    tree = tree_resp.json()
    blobs = [item for item in tree.get("tree", []) if item["type"] == "blob"]
    if not blobs:
        print(f"  No files in tree for {full_name}")
        return None

    files: List[Dict[str, Any]] = []
    for item in blobs:
        path = item["path"]
        if (
            path.lower().endswith("readme.md")
            or is_code_file(path)
            or os.path.basename(path) in ("requirements.txt", "setup.py", "pyproject.toml", "package.json")
        ):
            files.append(
                {
                    "path": path,
                    "size": item.get("size", 0),
                }
            )

    if not files:
        print(f"  No relevant files in {full_name}")
        return None

    files = sorted(files, key=lambda f: f["size"], reverse=True)[:MAX_FILES_PER_REPO]

    snapshot_files = []
    for f in files:
        path = f["path"]
        resp = rest_get(f"/repos/{owner}/{name}/contents/{path}", params={"ref": branch})
        if resp is None:
            continue
        data = resp.json()
        if data.get("type") != "file":
            continue

        content_b64 = data.get("content")
        if not content_b64:
            continue

        try:
            content_bytes = base64.b64decode(content_b64)
        except Exception:
            content_bytes = b""

        if len(content_bytes) > MAX_FILE_BYTES:
            content_bytes = content_bytes[:MAX_FILE_BYTES]

        try:
            content = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content = ""

        snapshot_files.append(
            {
                "path": path,
                "size": f["size"],
                "content": content,
            }
        )

    if not snapshot_files:
        print(f"  Could not fetch any file contents for {full_name}")
        return None

    snapshot = {
        "full_name": full_name,
        "url": repo["url"],
        "stars": repo["stars"],
        "disk_kb": repo["disk_kb"],
        "primary_language": repo["primary_language"],
        "default_branch": branch,
        "readme_score": repo["readme_score"],
    }

    return snapshot


def write_dataset(repos: List[Dict[str, Any]], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for r in repos:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n Wrote {len(repos)} repos to {path}")


def main():
    print(" Harvesting GitHub repositories for README-generation MAS dataset...\n")
    all_selected: List[Dict[str, Any]] = []
    for lang in LANGUAGES:
        print(f"\n Gathering candidates for language: {lang}")
        candidates = harvest_candidates(PER_LANG_TARGET * 6, languages=[lang])

        selected_for_lang: List[Dict[str, Any]] = []
        for thresh in (0.6, 0.5, 0.4):
            selected_for_lang = filter_and_score(candidates, PER_LANG_TARGET, min_score=thresh)
            if len(selected_for_lang) >= PER_LANG_TARGET:
                break

        if len(selected_for_lang) < PER_LANG_TARGET:
            print(f" Only found {len(selected_for_lang)} repos for {lang} after lowering thresholds.")

        all_selected.extend(selected_for_lang)

    if not all_selected:
        print("No repositories passed the README filters. Try adjusting queries or lowering score thresholds.")
        return

    uniq: Dict[str, Dict[str, Any]] = {}
    for r in all_selected:
        uniq[r["full_name"]] = r

    selected = list(uniq.values())
    print(f"\n Total selected repositories (deduped): {len(selected)}")

    final_snapshots: List[Dict[str, Any]] = []
    for i, repo in enumerate(selected, start=1):
        print(f" [{i}/{len(selected)}] Processing {repo['full_name']} (score={repo.get('readme_score')})")
        snap = snapshot_repo(repo)
        if snap:
            final_snapshots.append(snap)
        time.sleep(0.3)

    if final_snapshots:
        write_dataset(final_snapshots, DATASET_PATH)
    else:
        print("No repositories were successfully snapshotted. Check logs and try again.")


if __name__ == "__main__":
    main()
