"""
Batch pipeline: single-agent baseline generation → evaluation for a range of repos.

Runs the single-agent baseline (ablation_study/baseline_single_agent.py) for each
repository, then evaluates the generated README against the reference.

Usage:
    # Run repos 1–20
    python ablation_study/run_baseline_pipeline.py --start 1 --end 20

    # Run a single repo (e.g. repo #5)
    python ablation_study/run_baseline_pipeline.py --start 5 --end 5

    # Custom repo list file
    python ablation_study/run_baseline_pipeline.py --start 1 --end 20 --repos data/plan_repo_names.txt

    # Skip evaluation
    python ablation_study/run_baseline_pipeline.py --start 1 --end 20 --skip-eval
"""

import os
import sys
import argparse
import subprocess
import time

GENERATED_DIR = os.path.join("generated_readmes", "baseline_single_agent")
REF_DIR = os.path.join("data", "readmes")
EVAL_CSV = os.path.join("ablation_study", "baseline_single_agent_evaluation_results.csv")


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


def run_repo(repo_name: str, skip_eval: bool, model: str) -> dict:
    status = {"generation": "skipped", "evaluation": "skipped"}

    gen_cmd = [
        "python", "ablation_study/baseline_single_agent.py",
        "--repo_name", repo_name,
        "--model", model,
    ]
    ok = run_step("generation", gen_cmd)
    status["generation"] = "ok" if ok else "failed"
    if not ok:
        return status

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
                "--ref", ref_path,
                "--csv", EVAL_CSV,
            ])
            status["evaluation"] = "ok" if ok else "failed"

    return status


def main():
    parser = argparse.ArgumentParser(
        description="Batch pipeline: single-agent baseline generation → evaluation"
    )
    parser.add_argument(
        "--start", type=int, default=1,
        help="First repo to process (1-indexed, inclusive). Default: 1",
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="Last repo to process (1-indexed, inclusive). Default: last repo in list",
    )
    parser.add_argument(
        "--repos", default="data/plan_repo_names.txt",
        help="Path to repo names file, one per line. Default: data/plan_repo_names.txt",
    )
    parser.add_argument(
        "--model", type=str, default="gpt-5.1",
        help="Model to use for generation (default: gpt-5.1)",
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip evaluation step for all repos",
    )
    args = parser.parse_args()

    if not os.path.exists(args.repos):
        print(f"Error: {args.repos} not found.", file=sys.stderr)
        sys.exit(1)

    all_repos = load_repos(args.repos)
    total = len(all_repos)

    start_idx = args.start - 1
    end_idx = (args.end or total) - 1

    if start_idx < 0 or start_idx >= total:
        print(f"Error: --start {args.start} is out of range (1–{total})", file=sys.stderr)
        sys.exit(1)
    if end_idx >= total:
        print(f"Warning: --end {args.end} exceeds list size ({total}). Clamping to {total}.")
        end_idx = total - 1

    selected = all_repos[start_idx:end_idx + 1]
    print(f"\n{'='*60}")
    print(f"Single-Agent Baseline Pipeline: repos {args.start}–{args.end or total} ({len(selected)} repos)")
    print(f"Model: {args.model}")
    print(f"{'='*60}\n")

    results = {}
    t0 = time.time()

    for i, repo_name in enumerate(selected, start=args.start):
        print(f"\n[{i}/{args.end or total}] {repo_name}")
        print(f"  {'-'*50}")
        repo_status = run_repo(repo_name, args.skip_eval, args.model)
        results[repo_name] = repo_status

    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"Summary ({len(selected)} repos, {elapsed:.1f}s)")
    print(f"{'='*60}")
    failed = []
    for repo, s in results.items():
        icons = {"ok": "✓", "failed": "✗", "skipped": "–"}
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

    if not args.skip_eval and os.path.exists(EVAL_CSV):
        print(f"\nEvaluation results: {EVAL_CSV}")
    print(f"Token stats: ablation_study/baseline_single_agent_token_stats.csv")


if __name__ == "__main__":
    main()
