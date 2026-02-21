import os
import json
import re
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

class Aggregator:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/aggregator_prompt.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def _deduplicate_commands(self, content: str) -> str:
        """
        Post-processing: Remove duplicate command blocks that appear multiple times.
        This is a safety net for obvious duplicates the LLM might miss.
        """
        lines = content.split('\n')
        seen_commands = set()
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            # Detect code blocks with commands (npm, pip, git, etc.)
            if re.match(r'^\s*```', line):
                # Start of code block - collect the entire block
                code_block = [line]
                block_content = ""
                i += 1
                
                # Collect lines until we find the closing ```
                while i < len(lines):
                    code_block.append(lines[i])
                    if re.match(r'^\s*```', lines[i]):
                        # Found closing ```
                        break
                    block_content += lines[i] + "\n"
                    i += 1
                
                # Normalize block content for comparison (remove whitespace, case-insensitive)
                normalized = re.sub(r'\s+', ' ', block_content.strip().lower())
                
                # If we've seen this exact command pattern before, skip it
                if normalized in seen_commands and len(normalized) > 10:
                    print(f"Removing duplicate command block: {normalized[:50]}...")
                    i += 1
                    continue
                
                seen_commands.add(normalized)
                result_lines.extend(code_block)
                i += 1
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)

    def aggregate(self, sections: Dict[str, str]) -> str:
        print("Aggregating final README...")
        
        sections_str = json.dumps(sections, indent=2)

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["sections_json"]
        )
        
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({"sections_json": sections_str})
            content = result.content
            
            content = self._deduplicate_commands(content)
            
            return content
        except Exception as e:
            print(f"Aggregation failed: {e}")
            return "\n\n".join(sections.values())
