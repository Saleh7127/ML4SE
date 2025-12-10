"""
Call an LLM via LangChain to derive a common README pattern from heading JSONL.

Usage:
    python scripts/generate_pattern_via_llm.py \
        --input data/readme_headings.jsonl \
        --model gpt-4o-mini \
        --max-repos 20
"""

import argparse
import json
import os 
from dotenv import load_dotenv
from pathlib import Path
from typing import List

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


load_dotenv()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use an LLM to derive a common README pattern.")
    parser.add_argument("--input", default="data/readme_headings.jsonl", help="Heading JSONL produced by extract_headings.py")
    parser.add_argument("--model", default="gpt-5.1", help="Chat model name")
    parser.add_argument("--temperature", type=float, default=0, help="LLM temperature")
    parser.add_argument("--max-repos", type=int, default=20, help="Limit how many repos to include in the prompt")
    parser.add_argument("--output", default="data/2readme_pattern_llm.json", help="Where to write the pattern JSON.")
    return parser.parse_args()


def load_samples(path: Path, limit: int) -> List[dict]:
    samples: List[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if len(samples) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return samples


def format_headings(sample: dict) -> str:
    parts = []
    for h in sample.get("headings", []):
        lvl = h.get("level")
        text = h.get("text", "")
        parts.append(f"h{lvl}:{text}")
    return f"{sample.get('repo', 'unknown')}: " + " | ".join(parts)


def build_prompt(samples: List[dict]) -> str:
    formatted = "\n".join(format_headings(s) for s in samples)
    return f"""You are analyzing README structures.
Given a set of README heading sequences, infer a generalized README outline based on frequency patterns across projects. 
Your output must be a JSON object containing:

1. outline:
   - always_present: list of sections that appear in almost all READMEs.
   - very_common: list of sections that appear in many READMEs.
   - optional: sections that appear sometimes or rarely.
   Each section must include:
     • id: unique machine-friendly identifier  
     • title: human-readable section name  
     • purpose: short description of why this section exists  

2. template:
   A complete recommended README outline using the inferred structure 
   (similar to a standard README template).  
   Return it as an ordered list of section titles.

READMES:
{formatted}
"""


def call_llm(prompt: str, model_name: str, temperature: float) -> str:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    messages = [
        SystemMessage(content="You infer README section templates from heading lists and respond with JSON only."),
        HumanMessage(content=prompt),
    ]
    resp = llm.invoke(messages)
    return resp.content


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    samples = load_samples(input_path, args.max_repos)
    if not samples:
        raise SystemExit(f"No samples found in {input_path}")
    prompt = build_prompt(samples)
    output = call_llm(prompt, args.model, args.temperature)

    try:
        pattern = json.loads(output)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"LLM response was not valid JSON: {exc}\nResponse: {output[:500]}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(pattern, f, ensure_ascii=False, indent=2)
    print(f"Wrote pattern JSON to {output_path}")


if __name__ == "__main__":
    main()
