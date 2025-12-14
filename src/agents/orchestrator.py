import os
import json
from enum import Enum
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class OrchestratorDecision(BaseModel):
    decision: str = Field(..., description="Action to take: PROFILE, PLAN, DELEGATE, REVIEW, FINISH")
    reasoning: str = Field(..., description="Why this action?")
    target_sections: List[str] = Field(default_factory=list, description="Sections to process")
    instructions: Optional[str] = Field(None, description="Global instructions")

class Orchestrator:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1) # Low temp for logic
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/orchestrator_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def decide(self, state: Dict[str, Any]) -> OrchestratorDecision:
        print(f"[{state.get('repo_name')}] Orchestrator thinking...")
        
        # Prepare state for prompt
        section_status = state.get("section_status", {})
        feedback = state.get("review_feedback", {})
        
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["repo_name", "iteration", "phase", "has_profile", "has_plan", "section_status_json", "feedback_json"]
        )
        
        chain = prompt | self.llm.with_structured_output(OrchestratorDecision)
        
        # Hard Stop for Max Steps/Iterations (Safety Net)
        # Profile(1) -> Plan(2) -> Write(3) -> Review(4) -> Fix1(5) -> Rev1(6) -> ... -> Fix3(11) -> Rev3(12)
        if state.get("iteration", 0) >= 15:
            print(f"[{state.get('repo_name')}] Max steps (15) reached. Forcing finish.")
            return OrchestratorDecision(decision="FINISH", reasoning="Max steps reached.", target_sections=[])

        try:
            decision = chain.invoke({
                "repo_name": state.get("repo_name"),
                "iteration": state.get("iteration", 0),
                "phase": state.get("phase", "START"),
                "has_profile": state.get("profile") is not None,
                "has_plan": state.get("plan") is not None,
                "section_status_json": json.dumps(section_status, indent=2),
                "feedback_json": json.dumps(feedback, indent=2)
            })
            print(f"Orchestrator Decision: {decision.decision} ({decision.reasoning})")
            return decision
        except Exception as e:
            print(f"Orchestrator logic failed: {e}")
            # Safe Fallback: If nothing exists, Profile. If Profile, Plan. Etc.
            # This is hard to fallback safely without loops, but good enough for now.
            return OrchestratorDecision(decision="FINISH", reasoning="Error in decision logic.")
