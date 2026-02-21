
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
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/unified_profiler_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def profile(self, repo_name: str, file_tree: str) -> RepoProfile:
        print(f"[{repo_name}] Orchestrator Profiler running...")
        
        context = ""
        try:
            store = get_vector_store(repo_name)
            retriever = get_retriever(store)
            queries = [
                "project description purpose overview what is this",
                "installation setup requirements dependencies how to install",
                "usage examples features configuration how to use",
            ]
            all_docs, seen = [], set()
            for q in queries:
                for d in retriever.invoke(q)[:4]:
                    if d.page_content not in seen:
                        seen.add(d.page_content)
                        all_docs.append(d)
            context = "\n\n".join([f"...{d.page_content}..." for d in all_docs[:10]])
        except Exception as e:
            print(f"Vector Store access failed: {e}")
            context = "Vector store unavailable."

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "file_tree", "context"]
        )
        
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
