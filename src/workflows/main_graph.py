import operator
from typing import TypedDict, Annotated, List, Dict, Any, Union
from langgraph.graph import StateGraph, END, START
from langgraph.constants import Send

from src.models.repo_profile import RepoProfile
from src.models.readme_plan import ReadmePlan, ReadmeSectionResult
from src.models.review import ReviewFeedback

from src.agents.profilers.profile_builder import ProfileBuilder
from src.agents.readme_planner import ReadmePlanner
from src.agents.writers.core_writer import CoreWriter
from src.agents.writers.docs_writer import DocsWriter
from src.agents.writers.meta_writer import MetaWriter
from src.agents.writers.optional_writer import OptionalWriter
from src.agents.reviewers.factual_reviewer import FactualReviewer
from src.agents.reviewers.style_reviewer import StyleReviewer
from src.agents.aggregator import Aggregator

# --- State Definitions ---

class SectionState(TypedDict):
    section: ReadmeSectionResult
    content: str
    feedback: List[ReviewFeedback]
    iteration: int
    repo_profile: RepoProfile

class WorkflowState(TypedDict):
    repo_name: str
    repo_path: str
    profile: RepoProfile
    plan: ReadmePlan
    sections_content: Annotated[Dict[str, str], lambda x, y: {**x, **y}]
    section_status: Annotated[Dict[str, str], lambda x, y: {**x, **y}] # 'pending', 'pass', 'fail'
    review_feedback: Annotated[Dict[str, str], lambda x, y: {**x, **y}] # combined feedback string
    iteration: int

# --- Node Functions ---

def run_profiler(state: WorkflowState):
    builder = ProfileBuilder()
    profile = builder.build(state["repo_name"], state["repo_path"])
    return {
        "profile": profile,
        "iteration": 0,
        "sections_content": {},
        "section_status": {},
        "review_feedback": {}
    }

def route_to_writers_unused(state: WorkflowState):
    # Fan-out to writers for each enabled section
    sections = [s for s in state["plan"].sections if s.enabled]
    return [Send("write_section", {
        "section": s,
        "content": state["sections_content"].get(s.id, ""),
        "feedback": [], 
        "iteration": state["iteration"],
        "repo_profile": state["profile"]
    }) for s in sections]

def write_section_node_unused(state: SectionState):
    # Unused linear version
    pass

def route_to_reviewers_unused(state: WorkflowState):
    pass

def review_section_node_unused(state: SectionState):
    pass

# For simplicity in this first iteration, I will implement a LINEAR flow first:
# Profiler -> Planner -> Writers (Parallel) -> Aggregator.
# The Feedback loop adds significant complexity to the graph state management (managing map-reduce over iterations).
# Given the "don't overestimate" instruction, I'll stick to a clean v1 pipeline first, then add the loop if requested or if easy.
# Actually, the user REQUESTED the feedback loop explicitly.
# "Reviewer agents... feedback loop (max 3 rounds)".
# To support this, I need to know which sections failed and re-send ONLY them.

# Revised Approach for Graph:
# 1. Profiler -> Planner
# 2. Loop Start
# 3. Identify pending sections (all at start, failed ones later)
# 4. Fan out to Writers for pending sections
# 5. Join (update content)
# 6. Fan out to Reviewers for just-written sections
# 7. Join (collect failures)
# 8. Check: if no failures or max iter -> Aggregator -> End
# 9. Else -> Iterate

# WorkflowState moved to top

def init_node(state: WorkflowState):
    return {"iteration": 0, "sections_content": {}, "section_status": {}, "review_feedback": {}}

def generate_plan_node(state: WorkflowState):
    planner = ReadmePlanner()
    plan = planner.plan(state["profile"])
    # Initialize status for all enabled sections to 'pending'
    status = {s.id: "pending" for s in plan.sections if s.enabled}
    return {"plan": plan, "section_status": status}

def get_sections_to_write(state: WorkflowState):
    # Return list of Send objects for sections that are 'pending' or 'fail'
    # Wait, 'fail' sections need feedback passed to them.
    to_process = []
    for s in state["plan"].sections:
        if not s.enabled: continue
        status = state["section_status"].get(s.id, "pending")
        if status in ["pending", "fail"]:
            to_process.append(Send("write_node", {
                "section": s,
                "repo_profile": state["profile"],
                "feedback": state["review_feedback"].get(s.id, "")
            }))
    return to_process

def write_node_impl(state: dict): # Reduced state
    section = state["section"]
    profile = state["repo_profile"]
    feedback = state.get("feedback", "")
    
    # Logic to select writer...
    # Logic to select writer...
    if section.id in ["project_overview", "features", "installation", "requirements_dependencies"]:
        writer = CoreWriter()
    elif section.id in ["usage", "examples", "configuration", "api_reference", "advanced_usage", "project_structure", "performance", "testing", "cli_gui_tools"]:
        writer = DocsWriter()
    elif section.id in ["contributing", "license", "acknowledgments_credits", "contact_author"]:
        writer = MetaWriter()
    else:
        writer = OptionalWriter()

    instructions = (section.instructions or "") + ("\nFeedback to address: " + feedback if feedback else "")
    content = writer.write(profile, section.title or section.id, instructions)
    
    return {"sections_content": {section.id: content}, "section_status": {section.id: "written"}}

def get_sections_to_review(state: WorkflowState):
    # Review only sections that are 'written' (just updated)
    # Actually, we should review anything that isn't 'pass'.
    to_process = []
    for s in state["plan"].sections:
        if not s.enabled: continue
        if state["section_status"].get(s.id) == "written":
            to_process.append(Send("review_node", {
                "section": s,
                "content": state["sections_content"][s.id],
                "repo_profile": state["profile"]
            }))
    return to_process

def review_node_impl(state: dict):
    section = state["section"]
    content = state["content"]
    profile = state["repo_profile"]
    
    factual = FactualReviewer()
    style = StyleReviewer()
    
    f = factual.review(profile.name, section.id, content)
    s = style.review(section.id, content)
    
    combined_feedback = ""
    status = "pass"
    
    if f.status == "fail":
        status = "fail"
        combined_feedback += f"Technical Issues: {f.feedback}. "
    if s.status == "fail":
        status = "fail"
        combined_feedback += f"Style Issues: {s.feedback}."
        
    return {
        "section_status": {section.id: status},
        "review_feedback": {section.id: combined_feedback}
    }

def check_convergence(state: WorkflowState):
    # Check if all enabled sections are 'pass' or iteration >= 3
    all_passed = True
    for s in state["plan"].sections:
        if s.enabled and state["section_status"].get(s.id) != "pass":
            all_passed = False
            break
            
    if all_passed or state["iteration"] >= 2:
        return "aggregate"
    else:
        return "iterate"

def increment_iteration(state: WorkflowState):
    return {"iteration": state["iteration"] + 1}

def aggregate_node(state: WorkflowState):
    aggregator = Aggregator()
    # Sort content by plan order
    ordered_content = []
    for s in state["plan"].sections:
        if s.enabled and s.id in state["sections_content"]:
            ordered_content.append({"content": state["sections_content"][s.id]})
            
    final_md = aggregator.aggregate(ordered_content)
    # Save file
    import os
    output_dir = os.path.join(os.getcwd(), "readmes", state["repo_name"])
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "README.md")
    with open(output_path, "w") as f:
        f.write(final_md)
        
    return {"repo_path": output_path} # Return path of generated readme

# --- Graph Construction ---

workflow = StateGraph(WorkflowState)

workflow.add_node("profiler", run_profiler)
workflow.add_node("planner", generate_plan_node)
workflow.add_node("write_node", write_node_impl)
workflow.add_node("review_node", review_node_impl)
workflow.add_node("aggregator", aggregate_node)
workflow.add_node("next_iter", increment_iteration)

workflow.add_edge(START, "profiler")
workflow.add_edge("profiler", "planner")

# Fan out to writers
workflow.add_conditional_edges("planner", get_sections_to_write, ["write_node"])
workflow.add_conditional_edges("next_iter", get_sections_to_write, ["write_node"])

# Fan out to reviewers (from write_node? No, need to collect writes first)
# Use a dummy node or allow write_node to fan out directly? 
# LangGraph doesn't support implicit barrier easily without a collector node.
# We need a 'join' node effectively. 
# But map-reduce in LangGraph usually behaves such that if I return a Send, it goes there.
# I need to synchronize. 
# Best pattern: 
# Planner -> Writer (Map) -> Results. 
# Then Results -> Reviewer (Map) -> Status. 
# But Writer is parallel.
# I'll let the edges converge to a 'monitor' node.

# Let's simplify: 
# 1. Planner -> Writers (Map w/ explicit key)
# 2. Writers -> Reviewers (Map) -- Wait, Reviewer needs the output of Writer.
# This structure is getting complex for a single file.
# I will implement the LINEAR version + simple Aggregator for V1 to ensure it works, 
# as creating a robust loop with Map-Reduce in LangGraph requires careful state reducing which is error-prone without testing.
# The user asked for "Reviewer Agents... Feedback loop".
# I'll implement the loop logic inside a "ReviewManager" usage if Graph is too hard, BUT I should stick to LangGraph.

# Correct Pattern for Parallel Processing:
# Use `Send` to spawn branches. The graph waits for all branches to merge back to the state.
# So `write_node` writes to `sections_content`.
# Then we need a node to trigger the review phase.
# Let's add `trigger_review` node.

def trigger_review(state): return {} # Pass through

workflow.add_node("trigger_review", trigger_review)

# Edges:
# write_node is a destination of conditional edge.
# After all write_nodes done, where does it go?
# LangGraph map-reduce: we need a node that these branches lead to?
# Actually no, we just define the edge from `write_node` to `trigger_review`.

workflow.add_edge("write_node", "trigger_review")
workflow.add_conditional_edges("trigger_review", get_sections_to_review, ["review_node"])

def trigger_assessment(state): return {}
workflow.add_node("assess", trigger_assessment)
workflow.add_edge("review_node", "assess")

workflow.add_conditional_edges(
    "assess", 
    check_convergence,
    {
        "aggregate": "aggregator",
        "iterate": "next_iter"
    }
)

workflow.add_edge("aggregator", END)

app = workflow.compile()


