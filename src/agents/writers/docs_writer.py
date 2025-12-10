import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.models.repo_profile import RepoProfile
from src.vector_store.store import get_retriever, get_vector_store

class DocsWriter:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/writers/docs_writer.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def write(self, profile: RepoProfile, section_title: str, instructions: str = "") -> str:
        print(f"[{profile.name}] 3.2 Docs Writer: {section_title}...")
        
        context = ""
        try:
            store = get_vector_store(profile.name)
            retriever = get_retriever(store)
            # Targeted retrieval
            docs = retriever.invoke(f"{section_title} usage examples configuration code snippets")
            context = "\n".join([d.page_content[:500] for d in docs])
        except Exception:
            pass

        # Truncate profile for Docs Writer
        profile_copy = profile.model_copy()
        if len(profile_copy.commands) > 5:
            profile_copy.commands = profile_copy.commands[:5] + ["... (and more)"]
        if len(profile_copy.usage_snippets) > 3:
            profile_copy.usage_snippets = profile_copy.usage_snippets[:3] + ["... (and more)"]
        if len(profile_copy.config_options) > 10:
            profile_copy.config_options = profile_copy.config_options[:10] + ["... (and more)"]

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_profile_json", "section_title", "context", "instructions"]
        )
        
        chain = prompt | self.llm
        
        response = chain.invoke({
            "repo_profile_json": profile_copy.model_dump_json(),
            "section_title": section_title,
            "context": context,
            "instructions": instructions
        })
        
        return response.content
