from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RepoProfile(BaseModel):
    """
    Structured profile of the repository.
    """
    name: str = Field(..., description="Name of the repository.")
    type: str = Field(..., description="Type of project (e.g., 'cli_tool', 'library', 'web_service').")
    main_language: str = Field(..., description="Primary programming language.")

    description: Optional[str] = Field(None, description="One-line project description extracted verbatim from package.json, pyproject.toml, setup.py, Cargo.toml, etc. Do NOT paraphrase.")
    license_name: Optional[str] = Field(None, description="SPDX license identifier (e.g. 'MIT', 'Apache-2.0'). Extracted from LICENSE file or manifest.")
    homepage_url: Optional[str] = Field(None, description="Project homepage, docs site, or demo URL if explicitly listed in the manifest or README header.")
    dependencies: List[str] = Field(default_factory=list, description="Top 5 key runtime dependencies by name (e.g. 'fastapi', 'react', 'tokio').")

    install_methods: List[str] = Field(default_factory=list, description="Commands to install the project.")
    commands: List[str] = Field(default_factory=list, description="CLI commands or entry points.")

    has_examples: bool = Field(False, description="Whether usage examples exist.")
    usage_snippets: List[str] = Field(default_factory=list, description="Extracted code snippets showing usage.")

    config_options: List[str] = Field(default_factory=list, description="Configuration keys, env vars, or defaults.")

    key_features: List[str] = Field(default_factory=list, description="List of key features.")
    audience: str = Field("Developers", description="Intended audience.")
    has_contributing: bool = Field(False, description="Whether a CONTRIBUTING.md file or contributing section exists.")
    has_changelog: bool = Field(False, description="Whether a CHANGELOG.md or release notes file exists.")
