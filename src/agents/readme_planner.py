import os
import json
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from src.models.repo_profile import RepoProfile
from src.models.readme_plan import ReadmePlan

class ReadmePlanner:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/planner_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "readme_pattern_llm.json")
        with open(data_path, "r") as f:
            self.pattern_library = json.load(f)

    def plan(self, profile: RepoProfile) -> ReadmePlan:
        print(f"[{profile.name}] Orchestrator Planner running...")
        
        profile_json = profile.model_dump_json()
        pattern_library_str = json.dumps(self.pattern_library, indent=2)

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_profile_json", "pattern_library_json"]
        )
        
        chain = prompt | self.llm.with_structured_output(ReadmePlan)
        
        try:
            return chain.invoke({
                "repo_profile_json": profile_json,
                "pattern_library_json": pattern_library_str
            })
        except Exception as e:
            print(f"Planning failed: {e}")
            return ReadmePlan(sections=[])
