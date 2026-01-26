
import argparse
import os
import sys
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Add src to path
sys.path.append(os.getcwd())
from src.vector_store.store import get_vector_store

from dotenv import load_dotenv
load_dotenv()

def generate_single_agent_readme(repo_name: str, model_name: str = "gpt-5.1"):
    print(f"[{repo_name}] Starting Single-Agent Baseline Generation...")
    
    # 1. Retrieve Context
    print(f"[{repo_name}] Retrieving context from Vector Store...")
    try:
        store = get_vector_store(repo_name)
        retriever = store.as_retriever(search_type="mmr", search_kwargs={"k": 8})
        
        query = "project overview features installation instructions usage examples api configuration dependencies"
        docs = retriever.invoke(query)
        
        context_str = "\n\n".join([f"--- SOURCE: {d.metadata.get('source', 'unknown')} ---\n{d.page_content}" for d in docs])
        print(f"[{repo_name}] Retrieved {len(docs)} documents ({len(context_str)} chars).")
        
    except Exception as e:
        print(f"[{repo_name}] Error retrieving context: {e}")
        context_str = "No context available (Vector store error)."

    # 2. Prepare Prompt
    template = """You are an expert developer and technical writer. 
Your task is to write a comprehensive, professional README.md for the repository '{repo_name}'.

Here is the context related to the project retrieved from the codebase:

<Start_Context>
{context}
<End_Context>

Instructions:
1. Analyze the context to understand what the project does, how to install it, and how to use it.
2. Structure the README with standard sections: Title, Overview, Features, Installation, Usage, Configuration, Dependencies/Requirements.
3. Be specific. Use the actual code snippets from the context for installation commands and usage examples.
4. If you see specific installation commands (pip, npm, docker), use them.
5. If you see usage code, format it as code blocks.
6. Do not make up features that are not in the context.
7. Return ONLY the markdown content for the README.md.

Write the README.md now:
"""
    
    prompt = PromptTemplate(
        template=template, 
        input_variables=["repo_name", "context"]
    )
    
    print(f"[{repo_name}] Generating README (this may take a minute)...")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    chain = prompt | llm
    
    start_time = time.time()
    response = chain.invoke({
        "repo_name": repo_name,
        "context": context_str
    })
    duration = time.time() - start_time
    
    output_dir = os.path.join(os.getcwd(), "generated_readmes", "baseline_single_agent")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{repo_name}.md")
    
    with open(output_path, "w") as f:
        f.write(response.content)
        
    print(f"[{repo_name}] README generated successfully.")
    print(f"Saved to: {output_path}")
    print(f"Time Taken: {duration:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Single Agent Baseline for README Generation")
    parser.add_argument("--repo_name", type=str, required=True, help="Name of the ingested repository")
    parser.add_argument("--model", type=str, default="gpt-5.1", help="Model to use")
    
    args = parser.parse_args()
    
    generate_single_agent_readme(args.repo_name, args.model)
