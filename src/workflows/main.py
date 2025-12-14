import operator
import sys
import os
sys.path.append(os.getcwd())
from typing import TypedDict, Annotated, List, Dict, Any, Union
from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from langgraph.types import Send

from src.models.repo_profile import RepoProfile
from src.models.readme_plan import ReadmePlan, ReadmeSectionResult as ReadmeSection
from src.agents.orchestrator import Orchestrator, OrchestratorDecision
from src.agents.repo_profiler import UnifiedRepoProfiler
from src.agents.readme_planner import ReadmePlanner
from src.agents.writer_core import CoreWriter
from src.agents.writer_optional import OptionalWriter
from src.agents.reviewer import Reviewer
from src.agents.aggregator import Aggregator
from src.ingestion.utils.file_scanner import generate_file_tree


from dotenv import load_dotenv
load_dotenv()

class WorkflowState(TypedDict):
    repo_name: str
    repo_path: str
    
    plan: ReadmePlan | None
    sections_content: Annotated[Dict[str, str], lambda x, y: {**x, **y}]
    section_status: Annotated[Dict[str, str], lambda x, y: {**x, **y}] # 'pending', 'written', 'review_pending', 'pass', 'fail'
    review_feedback: Annotated[Dict[str, str], lambda x, y: {**x, **y}]
    
    iteration: int
    decision: OrchestratorDecision | None
    phase: str # PROFILE, PLAN, EXECUTION
    section_retries: Annotated[Dict[str, int], lambda x, y: {**x, **y}]

def orchestrator_node(state: WorkflowState):
    agent = Orchestrator()
    decision = agent.decide(state)
    return {"decision": decision, "iteration": state["iteration"] + 1}

def profiler_node(state: WorkflowState):
    agent = UnifiedRepoProfiler()

    file_tree = generate_file_tree(state["repo_path"], max_depth=2)
    
    profile = agent.profile(state["repo_name"], file_tree)
    return {"profile": profile, "phase": "PLANNING"}

def planner_node(state: WorkflowState):
    agent = ReadmePlanner()
    plan = agent.plan(state["profile"])
    status = {s.id: "pending" for s in plan.sections if s.enabled}
    return {"plan": plan, "section_status": status, "phase": "EXECUTION"}

def writer_dispatcher(state: WorkflowState):
    """
    Dispatcher to send to correct writer based on section type.
    This isn't a node, it's a conditional edge destination generator.
    """
    decision = state["decision"]
    targets = decision.target_sections
    
    tasks = []
    plan = state["plan"]
    
    for section in plan.sections:
        if section.id in targets:
            # Determine type
            if section.id in ["project_title", "project_overview", "features", "installation", "requirements_dependencies", "usage", "examples"]:
                tasks.append(Send("core_writer", {"section": section, "state": state}))
            else:
                tasks.append(Send("optional_writer", {"section": section, "state": state}))
    return tasks
class WriterInput(TypedDict):
    section: ReadmeSection
    state: WorkflowState

def core_writer_node(input: WriterInput):
    section = input["section"]
    state = input["state"]
    agent = CoreWriter()
    
    instructions = (section.instructions or "") + "\n" + (state["decision"].instructions or "")
    instructions = (section.instructions or "") + "\n" + (state["decision"].instructions or "")
    feedback = state["review_feedback"].get(section.id, "")
    if feedback:
        instructions += f"\n\nCRITICAL: Previous review feedback - {feedback}\n"
        instructions += "IMPORTANT: When rewriting, COMPLETELY REPLACE the current content. Do NOT append or merge. Remove any redundant information mentioned in the feedback."

    content = agent.write(state["profile"], section.title, instructions, current_content=state["sections_content"].get(section.id, ""))
    return {
        "sections_content": {section.id: content}, 
        "section_status": {section.id: "review_pending"}
    }

def optional_writer_node(input: WriterInput):
    section = input["section"]
    state = input["state"]
    agent = OptionalWriter()
    
    instructions = (section.instructions or "") + "\n" + (state["decision"].instructions or "")
    feedback = state["review_feedback"].get(section.id, "")
    if feedback:
        instructions += f"\n\nCRITICAL: Previous review feedback - {feedback}\n"
        instructions += "IMPORTANT: When rewriting, COMPLETELY REPLACE the current content. Do NOT append or merge. Remove any redundant information mentioned in the feedback."

    content = agent.write(state["profile"], section.title, instructions, current_content=state["sections_content"].get(section.id, ""))
    return {
        "sections_content": {section.id: content}, 
        "section_status": {section.id: "review_pending"}
    }

def reviewer_dispatcher(state: WorkflowState):
    decision = state["decision"]
    targets = decision.target_sections
    tasks = []
    plan = state["plan"]
    
    for section in plan.sections:
        if section.id in targets:
             tasks.append(Send("reviewer", {"section": section, "state": state}))
    return tasks

def reviewer_node(input: WriterInput):
    section = input["section"]
    state = input["state"]
    agent = Reviewer()
    
    content = state["sections_content"].get(section.id, "")
    result = agent.review(state["profile"], section.id, content)
    
    print(f"[{state['repo_name']}] Review for '{section.id}': {result.status}")
    if result.status == "fail":
        print(f"    Feedback: {result.feedback}")
    
    new_status = result.status
    
    # Handle Retries
    retries_map = state.get("section_retries", {})
    current_retries = retries_map.get(section.id, 0)
    
    updates = {}
    
    if new_status == "fail":
        current_retries += 1
        updates["section_retries"] = {section.id: current_retries}
        
        if current_retries >= 3:
            print(f"[{state['repo_name']}] Section '{section.id}' failed {current_retries} times. Max retries reached. Forcing PASS.")
            new_status = "pass"
    
    updates["section_status"] = {section.id: new_status}
    updates["review_feedback"] = {section.id: result.feedback}
    
    return updates

def aggregator_node(state: WorkflowState):
    agent = Aggregator()
    sections = {}
    for s in state["plan"].sections:
        if s.id in state["sections_content"]:
            sections[s.title] = state["sections_content"][s.id]
            
    final_md = agent.aggregate(sections)
    
    output_dir = os.path.join(os.getcwd(), "readmes", state["repo_name"])
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "README.md")
    with open(output_path, "w") as f:
        f.write(final_md)
        
    print(f"README generated at: {output_path}")
    return {"iteration": state["iteration"] + 1}



def route_orchestrator(state: WorkflowState):
    decision = state["decision"].decision
    if decision == "PROFILE":
        return "profiler"
    elif decision == "PLAN":
        return "planner"
    elif decision == "DELEGATE":
        return writer_dispatcher(state)
    elif decision == "REVIEW":
        return reviewer_dispatcher(state)
    elif decision == "FINISH":
        return "aggregator"
    else:
        return END



workflow = StateGraph(WorkflowState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("profiler", profiler_node)
workflow.add_node("planner", planner_node)
workflow.add_node("core_writer", core_writer_node)
workflow.add_node("optional_writer", optional_writer_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("aggregator", aggregator_node)

workflow.add_edge(START, "orchestrator")
workflow.add_edge("profiler", "orchestrator")
workflow.add_edge("planner", "orchestrator")
workflow.add_edge("core_writer", "orchestrator")
workflow.add_edge("optional_writer", "orchestrator")
workflow.add_edge("reviewer", "orchestrator")
workflow.add_edge("aggregator", END)

workflow.add_conditional_edges(
    "orchestrator",
    route_orchestrator,
    ["profiler", "planner", "core_writer", "optional_writer", "reviewer", "aggregator"]
)

app = workflow.compile()

if __name__ == "__main__":
    repo_name = "n8henrie__jupyter-black"
    repo_path = os.path.join(os.getcwd(), "data", "repositories", repo_name)
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository path does not exist: {repo_path}")
        print(f"Please ensure the repository is cloned to: data/repositories/{repo_name}")
        sys.exit(1)
    
    initial_state = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "iteration": 0,
        "sections_content": {},
        "section_status": {},
        "review_feedback": {},
        "section_retries": {}
    }
    
    print("Starting Orchestrator V2...")
    print(f"Repository: {repo_name}")
    print(f"Path: {repo_path}")
    for event in app.stream(initial_state):
        pass
