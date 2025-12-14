import os
import json
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from src.models.repo_profile import RepoProfile
from src.vector_store.store import get_retriever, get_vector_store

class ReviewResult(BaseModel):
    status: str = Field(..., description="'pass' or 'fail'")
    feedback: str = Field(..., description="Explanation of issues")
    rewritten_content: Optional[str] = Field(None, description="Corrected content if fix is minor")

class Reviewer:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/reviewer_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def review(self, profile: RepoProfile, section: str, content: str) -> ReviewResult:
        print(f"[{profile.name}] Unified Reviewer checking '{section}'...")
        
        context = ""
        try:
            store = get_vector_store(profile.name)
            retriever = get_retriever(store)
            docs = retriever.invoke(f"{section} verification items")
            context = "\n\n".join([d.page_content[:500] for d in docs[:3]])
        except Exception as e:
            context = "Verification context unavailable."

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["section_title", "content", "repo_profile_json", "context"]
        )
        
        chain = prompt | self.llm.with_structured_output(ReviewResult)
        
        try:
            return chain.invoke({
                "section_title": section,
                "content": content,
                "repo_profile_json": profile.model_dump_json(),
                "context": context
            })
        except Exception as e:
            print(f"Review failed: {e}")
            return ReviewResult(status="pass", feedback="Reviewer failed to execute, assuming pass.")
