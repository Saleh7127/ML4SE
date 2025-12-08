"""
Derive a common README section pattern from extracted heading JSONL.

Input JSONL (default: data/readme_headings.jsonl):
    {"repo": "...", "path": "...", "headings": [{"level": 1, "text": "Overview"}, ...]}

Output JSON (default: data/readme_pattern.json):
{
  "global_sections": [
    {"id": "intro", "title": "Overview", "purpose": "..."},
    ...
  ],
  "proposed_order": ["intro", "features", "install", ...],
  "meta": {"total_readmes": N}
}
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set


CANONICAL_SECTIONS = [
    {
        "id": "intro",
        "title": "Overview",
        "purpose": "Explain what the project is and why it exists",
        "keywords": ["overview", "introduction", "about", "what is", "summary"],
    },
    {
        "id": "features",
        "title": "Features",
        "purpose": "Highlight main capabilities",
        "keywords": ["feature", "capability", "highlights"],
    },
    {
        "id": "install",
        "title": "Installation",
        "purpose": "Explain how to install",
        "keywords": ["install", "installation", "setup", "requirements", "getting started", "quick start", "quickstart"],
    },
    {
        "id": "usage",
        "title": "Usage",
        "purpose": "Show basic usage",
        "keywords": ["usage", "use", "how to use", "run", "running", "how it works"],
    },
    {
        "id": "examples",
        "title": "Examples",
        "purpose": "Show extended examples",
        "keywords": ["example", "examples", "demo", "sample"],
    },
    {
        "id": "config",
        "title": "Configuration",
        "purpose": "Document config options",
        "keywords": ["config", "configuration", "settings", "options", "environment", "env"],
    },
    {
        "id": "contrib",
        "title": "Contributing",
        "purpose": "Explain how to contribute",
        "keywords": ["contributing", "contribution", "develop", "development", "roadmap"],
    },
    {
        "id": "license",
        "title": "License",
        "purpose": "State license",
        "keywords": ["license"],
    },
]

ID_TO_SECTION = {s["id"]: s for s in CANONICAL_SECTIONS}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def map_heading_to_id(text: str) -> Optional[str]:
    norm = normalize(text)
    for section in CANONICAL_SECTIONS:
        for kw in section["keywords"]:
            if kw in norm:
                return section["id"]
    return None


def load_records(path: Path) -> List[Dict]:
    records: List[Dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def aggregate_patterns(records: List[Dict]) -> Dict:
    counts: Dict[str, int] = defaultdict(int)
    pos_sum: Dict[str, int] = defaultdict(int)
    pos_count: Dict[str, int] = defaultdict(int)
    sequences: List[List[str]] = []

    for rec in records:
        seq: List[str] = []
        for heading in rec.get("headings", []):
            hid = map_heading_to_id(heading.get("text", ""))
            if not hid:
                continue
            if seq and seq[-1] == hid:
                continue
            seq.append(hid)
        if seq:
            sequences.append(seq)
            for idx, hid in enumerate(seq):
                counts[hid] += 1
                pos_sum[hid] += idx
                pos_count[hid] += 1

    avg_pos: Dict[str, float] = {}
    for hid in counts:
        avg_pos[hid] = pos_sum[hid] / max(pos_count[hid], 1)

    ordered_ids = sorted(counts.keys(), key=lambda hid: (avg_pos[hid], -counts[hid]))
    return {
        "counts": counts,
        "avg_pos": avg_pos,
        "ordered_ids": ordered_ids,
        "total_readmes": len(records),
    }


def build_pattern(agg: Dict, min_count: int) -> Dict:
    global_sections = []
    for sec in CANONICAL_SECTIONS:
        count = agg["counts"].get(sec["id"], 0)
        if count >= min_count:
            global_sections.append(
                {
                    "id": sec["id"],
                    "title": sec["title"],
                    "purpose": sec["purpose"],
                    "count": count,
                }
            )

    proposed_order: List[str] = [hid for hid in agg["ordered_ids"] if agg["counts"].get(hid, 0) >= min_count]

    return {
        "global_sections": global_sections,
        "proposed_order": proposed_order,
        "meta": {
            "total_readmes": agg["total_readmes"],
            "min_count": min_count,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive common README section patterns from heading JSONL.")
    parser.add_argument("--input", default="data/readme_headings.jsonl", help="Path to heading JSONL.")
    parser.add_argument("--output", default="data/readme_pattern_min_count.json", help="Where to write the pattern JSON.")
    parser.add_argument("--min-count", type=int, default=2, help="Minimum occurrence to include a section.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    records = load_records(input_path)
    if not records:
        raise SystemExit(f"No records found in {input_path}")

    agg = aggregate_patterns(records)
    pattern = build_pattern(agg, args.min_count)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(pattern, f, ensure_ascii=False, indent=2)
    print(f"Wrote README pattern to {output_path}")


if __name__ == "__main__":
    main()
