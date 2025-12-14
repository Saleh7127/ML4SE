
import os
import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from src.models.repo_profile import RepoProfile
from src.models.readme_plan import ReadmePlan
from src.vector_store.store import get_retriever, get_vector_store

class UnifiedRepoProfiler:
    def __init__(self, model_name: str = "gpt-5.1"):
        # Using a stronger model for the Unified Task if possible, or fallback to gpt-3.5-turbo/gpt-4
        # User config usually defaults.
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/unified_profiler_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def profile(self, repo_name: str, file_tree: str) -> RepoProfile:
        print(f"[{repo_name}] Orchestrator Profiler running...")
        
        # 1. Retrieve Context
        context = ""
        try:
            store = get_vector_store(repo_name)
            retriever = get_retriever(store)
            # Broad query to catch Installation, Usage, and Config
            docs = retriever.invoke("installation instructions usage examples configuration settings main features")
            # Limit context to avoid token overflow, but provide enough common chunks
            context = "\n\n".join([f"...{d.page_content}..." for d in docs[:5]])
        except Exception as e:
            print(f"Vector Store access failed: {e}")
            context = "Vector store unavailable."

        # 2. Invoke LLM
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "file_tree", "context"]
        )
        
        # We reuse the existing RepoProfile model which covers all fields
        chain = prompt | self.llm.with_structured_output(RepoProfile)
        
        try:
            profile = chain.invoke({
                "repo_name": repo_name,
                "file_tree": file_tree,
                "context": context
            })
            print(f"[{repo_name}] Profile generated successfully.")
            # Critical: Enforce the exact repo name from input to match Vector Store keys
            profile.name = repo_name 
            return profile
        except Exception as e:
            print(f"Profiling failed: {e}")
            # Return empty/fallback profile
            return RepoProfile(
                name=repo_name,
                type="Unknown",
                main_language="Unknown",
                audience="Developers",
                key_features=[],
                install_methods=[],
                commands=[],
                has_examples=False,
                usage_snippets=[],
                config_options=[]
            )
