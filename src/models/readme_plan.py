from typing import List, Optional
from pydantic import BaseModel, Field

class ReadmeSectionResult(BaseModel):
    id: str = Field(..., description="Section ID (e.g. 'intro', 'usage').")
    enabled: bool = Field(True, description="Whether to include this section.")
    title: Optional[str] = Field(None, description="Display title for the section.")
    instructions: Optional[str] = Field(None, description="Specific instructions for the writer.")

class ReadmePlan(BaseModel):
    """
    Structured plan for the README.
    """
    sections: List[ReadmeSectionResult] = Field(..., description="List of sections.")
