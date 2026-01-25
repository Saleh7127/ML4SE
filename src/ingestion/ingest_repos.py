import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingestion.utils.file_scanner import generate_file_tree
from src.ingestion.utils.librarian import identify_essential_files
from src.vector_store.store import ingest_repo
from dotenv import load_dotenv

load_dotenv()

# Process a single repository:
# python src/ingestion/ingest_repos.py --repos-dir <path/to/single-repo> --single-repo
# Multiple repositories in a directory.
# python src/ingestion/ingest_repos.py --repos-dir </path/to/repos-directory>
# Or use the default directory
# python src/ingestion/ingest_repos.py


def main():
    parser = argparse.ArgumentParser(description="Ingest repositories for ML4SE")
    parser.add_argument(
        "--repos-dir",
        type=str,
        default=os.path.join(os.getcwd(), "data", "repositories"),
        help="Path to the repositories directory or a single repository (default: ./data/repositories)"
    )
    parser.add_argument(
        "--single-repo",
        action="store_true",
        help="Treat --repos-dir as a single repository instead of a directory containing multiple repositories"
    )
    args = parser.parse_args()
    
    repos_dir = args.repos_dir
    if not os.path.exists(repos_dir):
        print(f"Path {repos_dir} does not exist.")
        return

    if args.single_repo:
        repo_name = os.path.basename(repos_dir)
        repo_path = repos_dir
        print(f"Processing single repository: {repo_name}")
        
        file_tree = generate_file_tree(repo_path)
        
        print("Consulting Librarian...")
        essential_files = identify_essential_files(file_tree)
        print(f"Librarian identified {len(essential_files)} essential files: {essential_files}")
        
        if essential_files:
            ingest_repo(repo_name, essential_files, repo_path)
        else:
            print("No essential files identified. Skipping ingestion.")
    else:
        repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
        
        if not repos:
            print(f"No repositories found in {repos_dir}")
            return

        print(f"Found {len(repos)} repositories: {repos}")

        for repo_name in repos:
            print(f"\nProcessing {repo_name}...")
            repo_path = os.path.join(repos_dir, repo_name)
            
            file_tree = generate_file_tree(repo_path)
            
            print("Consulting Librarian...")
            essential_files = identify_essential_files(file_tree)
            print(f"Librarian identified {len(essential_files)} essential files: {essential_files}")
            
            if essential_files:
                ingest_repo(repo_name, essential_files, repo_path)
            else:
                print("No essential files identified. Skipping ingestion.")

if __name__ == "__main__":
    main()
