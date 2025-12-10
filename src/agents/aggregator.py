from typing import List, Dict

class Aggregator:
    def aggregate(self, sections: List[Dict[str, str]]) -> str:
        """
        Combines section drafts into a final README.
        sections: List of dicts with 'content' key.
        """
        print(f"Aggregating {len(sections)} sections...")
        
        final_markdown = ""
        for section in sections:
            content = section.get("content", "").strip()
            if content:
                final_markdown += content + "\n\n"
        
        return final_markdown.strip()
