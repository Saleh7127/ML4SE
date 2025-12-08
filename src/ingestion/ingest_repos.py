import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingestion.utils.file_scanner import generate_file_tree
from src.ingestion.utils.librarian import identify_essential_files
from src.vector_store.store import ingest_repo
from dotenv import load_dotenv

load_dotenv()

def main():
    repos_dir = os.path.join(os.getcwd(), "data", "repositories")
    if not os.path.exists(repos_dir):
        print(f"Repository directory {repos_dir} does not exist.")
        return

    # List subdirectories (each is a repo)
    repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
    
    if not repos:
        print("No repositories found in data/repositories")
        return

    print(f"Found {len(repos)} repositories: {repos}")

    for repo_name in repos:
        print(f"\nProcessing {repo_name}...")
        repo_path = os.path.join(repos_dir, repo_name)
        
        # 1. Scan (Deterministic)
        file_tree = generate_file_tree(repo_path)
        print(f"File Tree generated.")
        
        # 2. Librarian (Agent)
        print("Consulting Librarian...")
        essential_files = identify_essential_files(file_tree)
        print(f"Librarian identified {len(essential_files)} essential files: {essential_files}")
        
        # 3. Ingest (Vector DB)
        if essential_files:
            ingest_repo(repo_name, essential_files, repo_path)
        else:
            print("No essential files identified. Skipping ingestion.")

if __name__ == "__main__":
    main()
