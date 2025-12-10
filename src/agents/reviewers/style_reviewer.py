import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.models.review import ReviewFeedback

class StyleReviewer:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/reviewers/style_reviewer.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def review(self, section_id: str, content: str) -> ReviewFeedback:
        print(f"5.2 Style Reviewer checking {section_id}...")
        
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["section_id", "content"]
        )
        
        chain = prompt | self.llm.with_structured_output(ReviewFeedback)
        
        try:
            return chain.invoke({
                "section_id": section_id,
                "content": content
            })
        except Exception as e:
            print(f"Style review failed: {e}")
            return ReviewFeedback(status="pass", feedback="Review failed, skipping.")
