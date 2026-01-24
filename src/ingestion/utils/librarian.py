import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def identify_essential_files(file_tree_str: str) -> list[str]:
    """
    Uses an LLM to identify essential files from a file tree string.
    """
    
    # Load prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "librarian_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt_template_str = f.read()

    prompt = PromptTemplate(
        template=prompt_template_str,
        input_variables=["file_tree"]
    )

    llm = ChatOpenAI(temperature=0.3, model_name="gpt-5-mini")

    chain = prompt | llm

    try:
        response = chain.invoke({"file_tree": file_tree_str})
        content = response.content.strip()
        
        # Handle potential markdown fencing
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        elif content.startswith("```"):
            content = content.replace("```", "")
            
        file_list = json.loads(content)
        return file_list
    except Exception as e:
        print(f"Error acting as Librarian: {e}")
        return []
