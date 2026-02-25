"""
Extracts repo names from readme_headings.jsonl.
The repo field is already in owner__repo format — no transformation needed.

Usage:
    python scripts/extract_repo_names.py
    python scripts/extract_repo_names.py --input data/readme_headings.jsonl
    python scripts/extract_repo_names.py --output my_repos.txt
"""

import json
import argparse
import os
import sys


def extract_repo_names(input_path: str) -> list[str]:
    repo_names = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            repo = entry.get("repo", "")
            if repo:
                repo_names.append(repo)
    return repo_names


def main():
    parser = argparse.ArgumentParser(description="Extract repo names from readme_headings.jsonl")
    parser.add_argument(
        "--input", "-i",
        default=os.path.join("data", "readme_headings.jsonl"),
        help="Path to the JSONL file (default: data/readme_headings.jsonl)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/repo_names.txt",
        help="Output file to write repo names, one per line. Prints to stdout if not set."
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.", file=sys.stderr)
        sys.exit(1)

    repo_names = extract_repo_names(args.input)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(repo_names) + "\n")
        print(f"Written {len(repo_names)} repo names to {args.output}")
    else:
        for name in repo_names:
            print(name)


if __name__ == "__main__":
    main()



# """
# Extracts repo names from repos_dataset.jsonl in the format owner__repo.

# Usage:
#     python scripts/extract_repo_names.py
#     python scripts/extract_repo_names.py --input data/repos_dataset.jsonl
#     python scripts/extract_repo_names.py --input data/repos_dataset.jsonl --output repo_names.txt
#     python scripts/extract_repo_names.py --language Python
#     python scripts/extract_repo_names.py --language Java --language Go
# """

# import json
# import argparse
# import os
# import sys

# def extract_repo_names(input_path: str, languages: list[str] = None) -> list[str]:
#     repo_names = []
#     with open(input_path, "r", encoding="utf-8") as f:
#         for line in f:
#             line = line.strip()
#             if not line:
#                 continue
#             entry = json.loads(line)
#             full_name = entry.get("full_name", "")
#             if not full_name:
#                 continue
#             if languages:
#                 lang = entry.get("primary_language", "")
#                 if lang not in languages:
#                     continue
#             repo_name = full_name.replace("/", "__")
#             repo_names.append(repo_name)
#     return repo_names


# def main():
#     parser = argparse.ArgumentParser(description="Extract repo names from repos_dataset.jsonl")
#     parser.add_argument(
#         "--input", "-i",
#         default=os.path.join("data", "repos_dataset.jsonl"),
#         help="Path to the JSONL file (default: data/repos_dataset.jsonl)"
#     )
#     parser.add_argument(
#         "--output", "-o",
#         default="data/repo_names.jsonl",
#         help="Output file to write repo names (one per line). Prints to stdout if not set."
#     )
#     parser.add_argument(
#         "--language", "-l",
#         action="append",
#         dest="languages",
#         metavar="LANG",
#         help="Filter by primary language (e.g. Python, JavaScript, Java, Go, C#). Repeatable."
#     )
#     args = parser.parse_args()

#     if not os.path.exists(args.input):
#         print(f"Error: {args.input} not found.", file=sys.stderr)
#         sys.exit(1)

#     repo_names = extract_repo_names(args.input, args.languages)

#     if args.output:
#         with open(args.output, "w", encoding="utf-8") as f:
#             f.write("\n".join(repo_names) + "\n")
#         print(f"Written {len(repo_names)} repo names to {args.output}")
#     else:
#         for name in repo_names:
#             print(name)


# if __name__ == "__main__":
#     main()
