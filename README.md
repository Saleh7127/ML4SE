# ML4SE

## Overview
ML4SE is a RAG-based Multi-Agent System designed to automatically generate comprehensive `README.md` files for local GitHub repositories. It utilizes a graph-based workflow to orchestrate specialized agents that analyze code, plan documentation structure, write content, and review the output.

## Features
- **Repository Profiling**: Analyzes the codebase structure and extracts key information.
- **Intelligent Planning**: Creates a tailored outline for the README based on the repository profile.
- **Multi-Agent Writing**: Uses specialized writers for different sections.
- **Automated Review**: Reviews generated content to ensure quality.
- **Graph-Based Workflow**: Orchestrated using LangGraph for robust state management.

## Usage
To run the system on a repository:

with the user README.md plan:
```bash
python src/workflows/main.py --repo_name sample_repository  --plan my_plan.json

```

without the user README.md plan:
```bash
python src/workflows/main.py --repo_name sample_repository

```

Ensure dependencies are installed and `.env` is configured with necessary API keys.