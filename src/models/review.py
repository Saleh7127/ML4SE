from typing import Optional
from pydantic import BaseModel, Field

class ReviewFeedback(BaseModel):
    status: str = Field(..., description="'pass' or 'fail'")
    feedback: str = Field(..., description="Explanation of the review.")
    fixed_content: Optional[str] = Field(None, description="Suggested rewritten content if applicable.")
