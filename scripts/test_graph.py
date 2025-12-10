import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.main_graph import app
from src.ingestion.utils.file_scanner import generate_file_tree
from dotenv import load_dotenv

load_dotenv()

def main():
    repo_name = "marzzuki__PlaylistBulletize"
    repo_path = os.path.join(os.getcwd(), "data", "repositories", repo_name)
    
    if not os.path.exists(repo_path):
        # Fallback to finding any repo
        repos_dir = os.path.join(os.getcwd(), "data", "repositories")
        if os.path.exists(repos_dir):
            repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
            if repos:
                repo_name = repos[0]
                repo_path = os.path.join(repos_dir, repo_name)
            else:
                print("No repositories found in data/repositories")
                return
        else:
             print("data/repositories directory missing")
             return

    print(f"Running graph for: {repo_name}")
    
    initial_state = {
        "repo_name": repo_name,
        "repo_path": repo_path
    }
    
    config = {"recursion_limit": 50}
    
    for event in app.stream(initial_state, config=config):
        for key, value in event.items():
            print(f"\n--- Output from {key} ---")
            if key == "profiler":
                print(f"Profile Type: {value.get('profile').type}")
            elif key == "planner":
                plan = value.get("plan")
                print(f"Plan Sections: {[s.id for s in plan.sections if s.enabled]}")
            elif key == "write_node":
                # value is Reduced state, showing partial updates
                pass
            elif key == "review_node":
                pass
            elif key == "aggregator":
                print(f"README generated at: {value.get('repo_path')}")

if __name__ == "__main__":
    main()
