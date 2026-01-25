# ML4SE

## Overview
ML4SE is a RAG-based Multi-Agent System designed to automatically generate comprehensive `README.md` files for local GitHub repositories. It utilizes a graph-based workflow to orchestrate specialized agents that analyze code, plan documentation structure, write content, and review the output.

## Features
- **Repository Profiling**: Analyzes the codebase structure and extracts key information.
- **Intelligent Planning**: Creates a tailored outline for the README based on the repository profile.
- **Multi-Agent Writing**: Uses specialized writers for different sections.
- **Automated Review**: Reviews generated content to ensure quality.
- **Graph-Based Workflow**: Orchestrated using LangGraph for robust state management.

## Setup

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Saleh7127/ML4SE.git
   cd ML4SE
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
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
--repos-dir /path/to/repos-directory
```

Or use the default directory (`./data/repositories`):
```bash
python src/ingestion/ingest_repos.py
```

#### Ingest a Single Repository
Process a specific repository:
```bash
python src/ingestion/ingest_repos.py \
--repos-dir /path/to/single-repo --single-repo
```

### Step 2: Generate README

Once repositories are ingested, generate README files using the main workflow:

#### With a Custom Plan
Provide your own README structure plan:
```bash
python src/workflows/main.py \
--repo_name sample_repository \
--plan my_plan.json
```

#### Without a Custom Plan
Let the system automatically create the structure:
```bash
python src/workflows/main.py \
--repo_name sample_repository
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
├── generated_readmes/              # Output directory for generated READMEs
├── generated_readmes_token_stats/  # Token usage statistics
├── scripts/                        # Utility scripts
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