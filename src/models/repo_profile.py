from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RepoProfile(BaseModel):
    """
    Structured profile of the repository.
    """
    name: str = Field(..., description="Name of the repository.")
    type: str = Field(..., description="Type of project (e.g., 'cli_tool', 'library', 'web_service').")
    main_language: str = Field(..., description="Primary programming language.")
    
    install_methods: List[str] = Field(default_factory=list, description="Commands to install the project.")
    commands: List[str] = Field(default_factory=list, description="CLI commands or entry points.")
    
    has_examples: bool = Field(False, description="Whether usage examples exist.")
    usage_snippets: List[str] = Field(default_factory=list, description="Extracted code snippets showing usage.")
    
    config_options: List[str] = Field(default_factory=list, description="Configuration keys, env vars, or defaults.")
    
    key_features: List[str] = Field(default_factory=list, description="List of key features.")
    audience: str = Field("Developers", description="Intended audience.")
