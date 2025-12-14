import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from src.models.repo_profile import RepoProfile
from src.vector_store.store import get_retriever, get_vector_store

class OptionalWriter:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2) # Slightly higher temp for creative sections
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/writer_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def write(self, profile: RepoProfile, section: str, instructions: str, **kwargs) -> str:
        print(f"[{profile.name}] OptionalWriter writing '{section}'...")
        
        # 1. Retrieve Context
        context = ""
        try:
            store = get_vector_store(profile.name)
            retriever = get_retriever(store)
            docs = retriever.invoke(f"{section} contribution license details")
            context = "\n\n".join([d.page_content[:1000] for d in docs[:3]])
        except Exception as e:
            # For optional sections, context might legitimately be missing, which is fine
            context = ""

        # 2. Generate
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["section_title", "section_type", "repo_profile_json", "instructions", "context", "current_content"]
        )
        
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({
                "section_title": section,
                "section_type": "optional",
                "repo_profile_json": profile.model_dump_json(),
                "instructions": instructions,
                "context": context,
                "current_content": kwargs.get("current_content", "")
            })
            return result.content
        except Exception as e:
            print(f"OptionalWriter failed on {section}: {e}")
            return "<!-- Failed to generate section -->"
