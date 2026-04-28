"""
Single-Agent Baseline for README Generation (Ablation Study).

This script generates a README.md for a given repository using a single LLM call
with a comprehensive prompt and retrieved codebase context. It serves as the
baseline condition in the ablation study, contrasting with the multi-agent (MAS)
pipeline that decomposes the task across specialized agents.

Usage:
    python single-agent/baseline_single_agent.py --repo_name <repo-name>
    python single-agent/baseline_single_agent.py --repo_name <repo-name> --model gpt-5.1
"""

import argparse
import csv
import os
import sys
import time
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.prompts import PromptTemplate

sys.path.append(os.getcwd())
from src.vector_store.store import get_vector_store, get_retriever

from dotenv import load_dotenv
load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(SCRIPT_DIR, "single_agent_prompt.txt")
TOKEN_STATS_PATH = os.path.join(SCRIPT_DIR, "baseline_single_agent_token_stats.csv")
OUTPUT_DIR = os.path.join(os.getcwd(), "generated_readmes", "baseline_single_agent")

# Retrieval queries — each targets a different facet of the repository so that
# the single agent receives broad, diverse context comparable to what the MAS
# pipeline gathers across its specialised agents.
RETRIEVAL_QUERIES = [
    "project overview description purpose architecture main entry point",
    "installation setup dependencies requirements pip npm docker compose",
    "usage examples commands API endpoints CLI flags run start",
    "configuration environment variables config options settings .env",
]


# Token counting callback (mirrors src/workflows/main.py)
class TokenCountingCallback(BaseCallbackHandler):
    """Accumulates token usage reported by the LLM provider."""

    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs):
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            self.total_tokens += usage.get("total_tokens", 0)
            self.prompt_tokens += usage.get("prompt_tokens", 0)
            self.completion_tokens += usage.get("completion_tokens", 0)


def retrieve_context(repo_name: str, k_per_query: int = 8) -> str:
    """
    Retrieve codebase context via multiple targeted queries against the
    repository's vector store.  Uses MMR (Maximal Marginal Relevance)
    retrieval to maximise diversity within each query, then deduplicates
    across queries by document content hash.

    Returns a single string containing all unique retrieved chunks,
    each prefixed with its source path.
    """
    print(f"[{repo_name}] Retrieving context from vector store ...")

    try:
        store = get_vector_store(repo_name)
        retriever = get_retriever(store)
    except Exception as e:
        print(f"[{repo_name}] ERROR: Could not load vector store — {e}")
        return "No context available (vector store error)."

    seen_contents: set = set()
    unique_docs: List = []

    for query in RETRIEVAL_QUERIES:
        try:
            docs = retriever.invoke(query)
        except Exception as e:
            print(f"[{repo_name}]  Warning: query failed ('{query[:40]}…'): {e}")
            continue

        for doc in docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_docs.append(doc)

    context_str = "\n\n".join(
        f"--- SOURCE: {d.metadata.get('source', 'unknown')} ---\n{d.page_content}"
        for d in unique_docs
    )

    print(
        f"[{repo_name}] Retrieved {len(unique_docs)} unique chunks "
        f"from {len(RETRIEVAL_QUERIES)} queries ({len(context_str):,} chars)."
    )
    return context_str


def load_prompt_template() -> PromptTemplate:
    """Load the external prompt file and return a LangChain PromptTemplate."""
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(
            f"Prompt file not found: {PROMPT_PATH}\n"
            "Expected file: ablation_study/single_agent_prompt.txt"
        )

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template_text = f.read()

    return PromptTemplate(
        template=template_text,
        input_variables=["repo_name", "context"],
    )


def append_token_stats(
    repo_name: str,
    duration_seconds: float,
    token_cb: TokenCountingCallback,
    model_name: str,
    context_chars: int,
    output_chars: int,
) -> None:
    """Append a row to the token-stats CSV (creates the file if needed)."""
    fieldnames = [
        "repo_name",
        "model",
        "duration_seconds",
        "total_tokens",
        "prompt_tokens",
        "completion_tokens",
        "context_chars",
        "output_chars",
    ]

    file_exists = os.path.exists(TOKEN_STATS_PATH)

    with open(TOKEN_STATS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "repo_name": repo_name,
            "model": model_name,
            "duration_seconds": round(duration_seconds, 2),
            "total_tokens": token_cb.total_tokens,
            "prompt_tokens": token_cb.prompt_tokens,
            "completion_tokens": token_cb.completion_tokens,
            "context_chars": context_chars,
            "output_chars": output_chars,
        })


def generate_single_agent_readme(repo_name: str, model_name: str = "gpt-5.1"):
    """
    End-to-end single-agent README generation:
      1. Retrieve context via multi-query strategy
      2. Load external prompt template
      3. Invoke LLM with token counting
      4. Save README and token stats
    """
    print("=" * 60)
    print(f"  Single-Agent Baseline — {repo_name}")
    print(f"  Model: {model_name}")
    print("=" * 60)

    t0 = time.time()
    context_str = retrieve_context(repo_name)
    retrieval_time = time.time() - t0
    print(f"[{repo_name}] Retrieval completed in {retrieval_time:.2f}s")

    prompt = load_prompt_template()

    print(f"[{repo_name}] Generating README (this may take a minute) ...")
    token_cb = TokenCountingCallback()
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        callbacks=[token_cb],
    )
    chain = prompt | llm

    generation_start = time.time()
    response = chain.invoke({
        "repo_name": repo_name,
        "context": context_str,
    })
    generation_time = time.time() - generation_start
    total_time = time.time() - t0

    readme_content = response.content
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{repo_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    append_token_stats(
        repo_name=repo_name,
        duration_seconds=total_time,
        token_cb=token_cb,
        model_name=model_name,
        context_chars=len(context_str),
        output_chars=len(readme_content),
    )

    print("-" * 60)
    print(f"  README saved to: {output_path}")
    print(f"  README length:   {len(readme_content):,} chars")
    print(f"  Retrieval time:  {retrieval_time:.2f}s")
    print(f"  Generation time: {generation_time:.2f}s")
    print(f"  Total time:      {total_time:.2f}s")
    print(f"  Prompt tokens:   {token_cb.prompt_tokens:,}")
    print(f"  Completion tokens: {token_cb.completion_tokens:,}")
    print(f"  Total tokens:    {token_cb.total_tokens:,}")
    print(f"  Token stats CSV: {TOKEN_STATS_PATH}")
    print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Single-Agent Baseline for README Generation (Ablation Study)"
    )
    parser.add_argument(
        "--repo_name",
        type=str,
        required=True,
        help="Name of the ingested repository (must have a vector store in knowledge_base/)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5.1",
        help="OpenAI model to use (default: gpt-5.1)",
    )

    args = parser.parse_args()
    generate_single_agent_readme(args.repo_name, args.model)
