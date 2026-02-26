"""
Batch pipeline: plan-based generation → evaluation for a range of repos.

This script is similar to run_pipeline.py but skips the ingestion step
(knowledge base already exists) and passes a plan JSON file to the
generation workflow.

Usage:
    # Run repos 1–20
    python scripts/run_plan_pipeline.py --start 1 --end 20

    # Run repos 21–40
    python scripts/run_plan_pipeline.py --start 21 --end 40

    # Run a single repo (e.g. repo #5)
    python scripts/run_plan_pipeline.py --start 5 --end 5

    # Custom repo list file
    python scripts/run_plan_pipeline.py --start 1 --end 20 --repos data/plan_repo_names.txt

    # Skip evaluation
    python scripts/run_plan_pipeline.py --start 1 --end 20 --skip-eval
"""

import os
import sys
import argparse
import subprocess
import time

PLAN_DIR = "readme-plan"
GENERATED_DIR = "plan_generated_readmes"
REF_DIR = "data/readmes"


def load_repos(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def run_step(label: str, cmd: list[str]) -> bool:
    """Run a subprocess step. Returns True on success, False on failure."""
    print(f"    [{label}] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"    [{label}] ✗ FAILED (exit code {result.returncode})")
        return False
    print(f"    [{label}] ✓ Done")
    return True


def run_repo(repo_name: str, skip_eval: bool) -> dict:
    status = {"generation": "skipped", "evaluation": "skipped"}

    # --- Generation with plan ---
    plan_path = os.path.join(PLAN_DIR, f"{repo_name}.json")
    if not os.path.exists(plan_path):
        print(f"    [generation] ✗ FAILED — plan not found at {plan_path}")
        status["generation"] = "failed"
        return status

    ok = run_step("generation", [
        "python", "src/workflows/main.py",
        "--repo_name", repo_name,
        "--plan", plan_path
    ])
    status["generation"] = "ok" if ok else "failed"
    if not ok:
        return status

    # --- Evaluation ---
    if skip_eval:
        print(f"    [evaluation] Skipped (--skip-eval)")
    else:
        gen_path = os.path.join(GENERATED_DIR, f"{repo_name}.md")
        ref_path = os.path.join(REF_DIR, f"{repo_name}.md")
        if not os.path.exists(ref_path):
            print(f"    [evaluation] Skipped — no reference README at {ref_path}")
            status["evaluation"] = "skipped"
        elif not os.path.exists(gen_path):
            print(f"    [evaluation] ✗ FAILED — generated README not found at {gen_path}")
            status["evaluation"] = "failed"
        else:
            ok = run_step("evaluation", [
                "python", "src/evaluation/evaluate_readme.py",
                "--repo", repo_name,
                "--gen", gen_path,
                "--ref", ref_path
            ])
            status["evaluation"] = "ok" if ok else "failed"

    return status


def main():
    parser = argparse.ArgumentParser(description="Batch pipeline: plan-based generation → evaluation")
    parser.add_argument("--start", type=int, default=1,
                        help="First repo to process (1-indexed, inclusive). Default: 1")
    parser.add_argument("--end", type=int, default=None,
                        help="Last repo to process (1-indexed, inclusive). Default: last repo in list")
    parser.add_argument("--repos", default="data/plan_repo_names.txt",
                        help="Path to repo names file, one per line. Default: data/plan_repo_names.txt")
    parser.add_argument("--skip-eval", action="store_true",
                        help="Skip evaluation step for all repos")
    args = parser.parse_args()

    if not os.path.exists(args.repos):
        print(f"Error: {args.repos} not found.", file=sys.stderr)
        sys.exit(1)

    all_repos = load_repos(args.repos)
    total = len(all_repos)

    start_idx = args.start - 1          # convert to 0-indexed
    end_idx = (args.end or total) - 1   # convert to 0-indexed, inclusive

    if start_idx < 0 or start_idx >= total:
        print(f"Error: --start {args.start} is out of range (1–{total})", file=sys.stderr)
        sys.exit(1)
    if end_idx >= total:
        print(f"Warning: --end {args.end} exceeds list size ({total}). Clamping to {total}.")
        end_idx = total - 1

    selected = all_repos[start_idx:end_idx + 1]
    print(f"\n{'='*60}")
    print(f"Plan Pipeline: repos {args.start}–{args.end or total} ({len(selected)} repos)")
    print(f"{'='*60}\n")

    results = {}
    t0 = time.time()

    for i, repo_name in enumerate(selected, start=args.start):
        print(f"\n[{i}/{args.end or total}] {repo_name}")
        print(f"  {'-'*50}")
        repo_status = run_repo(repo_name, args.skip_eval)
        results[repo_name] = repo_status

    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"Summary ({len(selected)} repos, {elapsed:.1f}s)")
    print(f"{'='*60}")
    failed = []
    for repo, s in results.items():
        icons = {
            "ok": "✓", "failed": "✗", "skipped": "–"
        }
        line = (
            f"  {icons.get(s['generation'], '?')} gen  "
            f"{icons.get(s['evaluation'], '?')} eval  — {repo}"
        )
        print(line)
        if "failed" in s.values():
            failed.append(repo)

    if failed:
        print(f"\n✗ {len(failed)} repos had failures:")
        for r in failed:
            print(f"    - {r}")
    else:
        print(f"\n✓ All repos completed successfully.")


if __name__ == "__main__":
    main()
