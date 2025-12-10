import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.vector_store.store import get_retriever, get_vector_store

class ConfigExtractionResult(BaseModel):
    config_options: List[str] = Field(default_factory=list)

class ConfigExtractor:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/profilers/config_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def extract(self, repo_name: str, file_tree: str) -> ConfigExtractionResult:
        print(f"[{repo_name}] 1.3 Config Extractor running...")
        
        # Retrieval step
        try:
            store = get_vector_store(repo_name)
            retriever = get_retriever(store)
            # Query for config info
            docs = retriever.invoke("configuration environment variables settings")
            context = "\n".join([d.page_content[:500] for d in docs])
        except Exception as e:
            print(f"Retriever unavailable for {repo_name}: {e}")
            context = "No retrieved context available."
            
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "file_tree", "context"]
        )
        
        chain = prompt | self.llm.with_structured_output(ConfigExtractionResult)
        
        try:
            return chain.invoke({
                "repo_name": repo_name, 
                "file_tree": file_tree,
                "context": context
            })
        except Exception as e:
            print(f"Config extraction failed: {e}")
            return ConfigExtractionResult()
