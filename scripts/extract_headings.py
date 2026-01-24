"""
Extract Markdown headings from README files and save them as JSONL.

Each JSONL line contains:
{
  "repo": "repo_name",
  "path": "data/readmes/repo_name.md",
  "headings": [{"level": 1, "text": "Title"}, ...]
}

Usage:
    python scripts/extract_headings.py \
        --readmes-dir data/readmes \
        --output data/readme_headings.jsonl
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
IMAGE_RE = re.compile(r"!\[[^\]]*]\([^)]+\)")
LINK_RE = re.compile(r"\[([^\]]+)]\([^)]+\)")
Bare_LINK_RE = re.compile(r"\[\s*]\([^)]+\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def clean_heading(text: str) -> str:
    """Remove badges/images, unwrap links, drop HTML anchors, and tidy whitespace."""
    text = IMAGE_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = Bare_LINK_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract headings from README files into JSONL.")
    parser.add_argument("--readmes-dir", default="data/readmes", help="Directory containing README copies.")
    parser.add_argument("--output", default="data/readme_headings.jsonl", help="Path to write JSONL output.")
    return parser.parse_args()


def extract_headings(path: Path) -> List[Dict[str, str]]:
    headings: List[Dict[str, str]] = []
    in_code = False
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.rstrip("\n")
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            match = HEADING_RE.match(stripped)
            if match:
                level = len(match.group(1))
                if level > 2:
                    continue
                raw_text = match.group(2).strip()
                text = clean_heading(raw_text)
                if text:
                    headings.append({"level": level, "text": text})
    return headings


def process_readmes(readmes_dir: Path, output_path: Path) -> int:
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for path in sorted(readmes_dir.glob("*.md"), key=lambda p: p.name.lower()):
            headings = extract_headings(path)
            record = {
                "repo": path.stem,
                "path": str(path),
                "headings": headings,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    args = parse_args()
    readmes_dir = Path(args.readmes_dir)
    if not readmes_dir.exists():
        raise SystemExit(f"Readmes directory not found: {readmes_dir}")
    output_path = Path(args.output)
    total = process_readmes(readmes_dir, output_path)
    print(f"Wrote headings for {total} README files to {output_path}")


if __name__ == "__main__":
    main()
