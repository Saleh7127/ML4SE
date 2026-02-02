import os
import argparse
from typing import Dict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

def read_file(file_path: str) -> str:
    """Reads the content of a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

def get_judge_model():
    """Initializes the Gemini model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.0,
        google_api_key=api_key
    )

def compare_readmes(readme1_content: str, readme2_content: str, criteria: str = "general") -> str:
    """Compares two README files using an LLM."""
    
    model = get_judge_model()
    
    system_prompt = """You are an expert software documentation reviewer. 
    Your task is to compare two README files and evaluate them based on specific criteria.
    
    You will be provided with the content of two README files:
    - README 1
    - README 2
    
    Please evaluate them based on the following dimensions:
    1. **Correctness**: Does the README accurately describe the project (based on the content provided)? Note: Since you don't have the full code, judge based on internal consistency and clarity of instructions.
    2. **Readability**: Is the language clear, concise, and easy to understand? Are there spelling or grammar errors?
    3. **Structure/Formatting**: Is the document well-structured with clear headings, lists, and code blocks?
    4. **Completeness**: Does it cover essential sections like Installation, Usage, Configuration, and Contributing?
    
    For each dimension, provide a score from 1 to 10 for each README, and a brief explanation.
    Finally, provide a summary comparison and declare a winner for each category and an overall winner.
    """
    
    user_prompt = """
    Here is the content of **README 1**:
    {readme1}
    
    --------------------------------------------------
    
    Here is the content of **README 2**:
    {readme2}
    
    Please provide your evaluation.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt)
    ])
    
    chain = prompt | model | StrOutputParser()
    
    result = chain.invoke({
        "readme1": readme1_content,
        "readme2": readme2_content
    })
    
    return result

def main():
    parser = argparse.ArgumentParser(description="LLM-as-Judge to compare two README files.")
    parser.add_argument("readme1_path", help="Path to the first README file")
    parser.add_argument("readme2_path", help="Path to the second README file")
    
    args = parser.parse_args()
    
    print(f"Reading README 1 from: {args.readme1_path}")
    content1 = read_file(args.readme1_path)
    if content1.startswith("Error reading file"):
        print(content1)
        return

    print(f"Reading README 2 from: {args.readme2_path}")
    content2 = read_file(args.readme2_path)
    if content2.startswith("Error reading file"):
        print(content2)
        return

    print("\nComparing READMEs... This may take a moment.\n")
    try:
        evaluation = compare_readmes(content1, content2)
        print("---------------- Evaluation Result ----------------")
        print(evaluation)
        print("---------------------------------------------------")
    except Exception as e:
        print(f"An error occurred during evaluation: {e}")

if __name__ == "__main__":
    main()
