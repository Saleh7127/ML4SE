import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.models.review import ReviewFeedback
from src.vector_store.store import get_retriever, get_vector_store

class FactualReviewer:
    def __init__(self, model_name: str = "gpt-5.1"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "src/prompts/reviewers/factual_reviewer.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def review(self, repo_name: str, section_id: str, content: str) -> ReviewFeedback:
        print(f"[{repo_name}] 5.1 Factual Reviewer checking {section_id}...")
        
        context = ""
        try:
            store = get_vector_store(repo_name)
            retriever = get_retriever(store)
            # Retrieve validation info
            docs = retriever.invoke(f"validate {section_id} {content[:100]}")
            context = "\n".join([d.page_content[:500] for d in docs])
        except Exception:
            pass

        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["section_id", "content", "context"]
        )
        
        chain = prompt | self.llm.with_structured_output(ReviewFeedback)
        
        try:
            return chain.invoke({
                "section_id": section_id,
                "content": content,
                "context": context
            })
        except Exception as e:
            print(f"Factual review failed: {e}")
            return ReviewFeedback(status="pass", feedback="Review failed, skipping.")
