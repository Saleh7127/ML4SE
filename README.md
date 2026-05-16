# Replication Package for README Generation with Single-Agent and Multi-Agent RAG Systems

## Overview

This repository contains the replication package for the paper:

**The Illusion of Agentic Complexity in README.md Generation: Evaluating Single-Agent vs. Multi-Agent RAG Systems**

The package implements and evaluates Retrieval-Augmented Generation (RAG) pipelines for automatically generating `README.md` files from local GitHub repositories. The study compares:

1. a **Single-Agent RAG pipeline**,
2. a **Multi-Agent System (MAS) pipeline**,
3. a **Developer-Guided Planning variant (Dev-Plan)**, and
4. the **LARCH baseline**.

The goal is to evaluate whether multi-agent decomposition improves repository-level README generation quality compared with a simpler single-agent design, and to measure the trade-off between quality, structural consistency, runtime, and token cost.

## Repository Contents

This package includes code for:

- preparing repositories for README generation,
- excluding original README and Markdown files before indexing,
- building repository-specific vector stores,
- generating README files using single-agent and multi-agent workflows,
- running developer-guided planning experiments,
- running baseline generation,
- evaluating generated READMEs using lexical and structural metrics.

## Pipeline Summary

The replication package follows four main stages.

### 1. Repository Preparation

The original `README.md` file is extracted and stored as the ground-truth reference. It is then excluded from the generation pipeline, along with other Markdown files, to prevent the models from directly accessing reference documentation.

### 2. Semantic Indexing

Each repository is processed into a local vector database. A file-selection component identifies relevant source and configuration files. Selected files are then split using language-aware chunking and embedded into isolated repository-specific collections.

### 3. README Generation

The package supports three README generation settings:

- **Single-Agent**: retrieves repository context and generates the full README in one prompt.
- **MAS**: uses multiple specialized agents for profiling, planning, section writing, review, and aggregation.
- **Dev-Plan**: replaces the autonomous planner with a manually supplied JSON plan while keeping the downstream MAS workflow unchanged.

### 4. Evaluation

Generated READMEs can be evaluated using:

- ROUGE,
- BERTScore,
- token usage,
- runtime,
- manual taxonomy coverage,
- LLM-as-a-Judge scoring.

## Setup

### 1. Clone the Anonymous Repository

```bash
git clone <anonymous-repository-url>
cd <repository-name>

### 2. Install Dependencies

```bash
pip install -r requirements.txt

### 3. Configure Environment Variables

Create a `.env` file in the root directory with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
```


## Usage

### Step 1: Ingest Repositories

Before generating README files, you need to ingest your repositories into the vector store. The ingestion script supports two modes:

#### Ingest Multiple Repositories (Default)
Process all repositories in a directory:
```bash
python src/ingestion/ingest_repos.py \
--repos-dir <path/to/repos-directory>
```

Or use the default directory (`./data/repositories`):
```bash
python src/ingestion/ingest_repos.py
```

#### Ingest a Single Repository
Process a specific repository:
```bash
python src/ingestion/ingest_repos.py \
--repos-dir <path/to/single-repo> --single-repo
```

### Step 2: Generate README

Once repositories are ingested, generate README files using the main workflow:


#### With Single Agent
```bash
python single-agent/baseline_single_agent.py \
--repo_name <repo-name>
```

#### With Multi Agent
```bash
python src/workflows/main.py \
--repo_name <repo-name>
```

#### With Multi Agent and Dev-guided Plan
```bash
python src/workflows/main.py \
--repo_name <repo-name> \
--plan <plan-name>.json
```

### Step 3: Evaluate

#### Run Automated Evaluation

```bash
python src/evaluation/evaluate_readme.py \
--repo <repo-name> \
--gen <gen-path> \
--ref <ref-path> 

```

## Command Reference

### Ingestion Commands
| Command | Description |
|---------|-------------|
| `ingest_repos.py` | Process repositories for ingestion |
| `--repos-dir <path>` | Path to repository or directory (default: `./data/repositories`) |
| `--single-repo` | Treat path as a single repository instead of a directory |

### Workflow Commands
| Command | Description |
|---------|-------------|
| `main.py` | Generate README for a repository |
| `--repo_name <name>` | Name of the repository to process |
| `--plan <file>` | Optional custom plan JSON file |

## Project Structure
```
ML4SE/
├── data/                           # Default location for repositories
├── scripts/                        # Utility scripts
├── single-agent/                   # Single agent baseline
├── src/
│   ├── agents/                     # Agent implementations
│   ├── evaluation/                 # Evaluation metrics and tools
│   ├── ingestion/                  # Repository ingestion and processing
│   ├── models/                     # Data models and schemas
│   ├── prompts/                    # Prompt templates
│   ├── vector_store/               # Vector database management
│   └── workflows/                  # Main workflow orchestration
└── requirements.txt                # Python dependencies
```


## Reproducing the Experiments

A typical reproduction workflow is:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add API key
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

# 3. Place repositories under data/repositories/

# 4. Ingest repositories - single repo or multiple repos

python src/ingestion/ingest_repos.py --repos-dir <path/to/repos-directory>

python src/ingestion/ingest_repos.py --repos-dir <path/to/single-repo> --single-repo


# 5. Run single-agent generation
python single-agent/baseline_single_agent.py --repo_name <repo-name>

# 6. Run multi-agent generation
python src/workflows/main.py --repo_name <repo-name>

# 7. Run developer-guided generation
python src/workflows/main.py --repo_name <repo-name> --plan <plan-name>.json
```

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.