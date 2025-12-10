import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class StructureInfo(BaseModel):
    type: str = Field(..., description="Project type (cli_tool, library, etc).")
    main_language: str = Field(..., description="Main programming language.")
    audience: str = Field(..., description="Intended audience.")
    key_features: List[str] = Field(default_factory=list, description="Inferred features.")

class StructureAnalyzer:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/profilers/structure_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def analyze(self, repo_name: str, file_tree: str) -> StructureInfo:
        print(f"[{repo_name}] 1.1 Structure Analyzer running...")
        
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "file_tree"]
        )
        
        chain = prompt | self.llm.with_structured_output(StructureInfo)
        
        try:
            return chain.invoke({"repo_name": repo_name, "file_tree": file_tree})
        except Exception as e:
            print(f"Structure analysis failed: {e}")
            return StructureInfo(type="unknown", main_language="unknown", audience="developers")
