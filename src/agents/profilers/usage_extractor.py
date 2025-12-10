import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.vector_store.store import get_retriever, get_vector_store

class UsageExtractionResult(BaseModel):
    install_commands: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)
    has_examples: bool = Field(False)
    usage_snippets: List[str] = Field(default_factory=list)

class UsageExtractor:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/profilers/usage_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def extract(self, repo_name: str, file_tree: str) -> UsageExtractionResult:
        print(f"[{repo_name}] 1.2 Usage Extractor running...")
        
        # Retrieval step
        try:
            store = get_vector_store(repo_name)
            retriever = get_retriever(store)
            # Query for broad usage info
            docs = retriever.invoke("how to install and run usage examples")
            context = "\n".join([d.page_content[:500] for d in docs]) # Limit context size
        except Exception as e:
            print(f"Retriever unavailable for {repo_name}: {e}")
            context = "No retrieved context available."
            
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "file_tree", "context"]
        )
        
        chain = prompt | self.llm.with_structured_output(UsageExtractionResult)
        
        try:
            return chain.invoke({
                "repo_name": repo_name, 
                "file_tree": file_tree,
                "context": context
            })
        except Exception as e:
            print(f"Usage extraction failed: {e}")
            return UsageExtractionResult()
