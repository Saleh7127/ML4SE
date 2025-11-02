import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GitHubAPI:
    def __init__(self, token=None):
        """
        Initialize GitHub API client
        token: Personal access token (optional for public repos)
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def get_repo_info(self, owner, repo):
        """Get basic information about a repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
            return None
    
    def get_repo_commits(self, owner, repo, limit=10):
        """Get recent commits from a repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    
    def get_repo_issues(self, owner, repo, state="open", limit=10):
        """Get issues from a repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": limit}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    
    def search_repositories(self, query, limit=10):
        """Search for repositories"""
        url = f"{self.base_url}/search/repositories"
        params = {"q": query, "per_page": limit}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None


def save_repo_info_to_file(owner, repo, output_file="repo_info.md"):
    """Fetch and save repository information to a markdown file"""
    
    # Get token from environment variable
    token = os.getenv("GITHUB_TOKEN")
    
    # Initialize API client
    gh = GitHubAPI(token)
    
    # Create output content
    content = []
    content.append(f"# {owner}/{repo} - Repository Information\n")
    content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    content.append("---\n")
    
    # Get repository information
    print(f"Fetching repository information for {owner}/{repo}...")
    repo_info = gh.get_repo_info(owner, repo)
    if repo_info:
        content.append("## Repository Details\n")
        content.append(f"- **Name:** {repo_info['name']}")
        content.append(f"- **Full Name:** {repo_info['full_name']}")
        content.append(f"- **Description:** {repo_info['description'] or 'No description'}")
        content.append(f"- **Stars:** {repo_info['stargazers_count']}")
        content.append(f"- **Forks:** {repo_info['forks_count']}")
        content.append(f"- **Language:** {repo_info['language'] or 'N/A'}")
        content.append(f"- **Open Issues:** {repo_info['open_issues_count']}")
        content.append(f"- **License:** {repo_info.get('license', {}).get('name', 'N/A')}")
        content.append(f"- **Created:** {repo_info['created_at']}")
        content.append(f"- **Updated:** {repo_info['updated_at']}")
        content.append(f"- **Clone URL:** {repo_info['clone_url']}")
        content.append(f"- **Homepage:** {repo_info['homepage'] or 'N/A'}")
        content.append(f"- **Default Branch:** {repo_info['default_branch']}")
        content.append(f"- **Repository URL:** {repo_info['html_url']}\n")
    else:
        content.append("### Error: Could not fetch repository information\n")
        return False
    
    # Get recent commits
    print(f"Fetching recent commits...")
    commits = gh.get_repo_commits(owner, repo, limit=10)
    if commits:
        content.append("## Recent Commits\n")
        for commit in commits:
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date']
            message = commit['commit']['message'].split('\n')[0]
            sha = commit['sha'][:7]
            content.append(f"- **{message}**")
            content.append(f"  - Author: {author}")
            content.append(f"  - Date: {date}")
            content.append(f"  - SHA: {sha}")
            content.append("")
    else:
        content.append("### No commits found\n")
    
    # Get open issues
    print(f"Fetching open issues...")
    issues = gh.get_repo_issues(owner, repo, state="open", limit=10)
    if issues:
        content.append("## Open Issues\n")
        for issue in issues:
            labels = ""
            if issue.get('labels'):
                labels = f" [{', '.join([label['name'] for label in issue['labels']])}]"
            content.append(f"- **#{issue['number']}:** {issue['title']}{labels}")
            content.append(f"  - State: {issue['state']}")
            content.append("")
    else:
        content.append("### No open issues found\n")
    
    # Get closed issues
    print(f"Fetching closed issues...")
    closed_issues = gh.get_repo_issues(owner, repo, state="closed", limit=10)
    if closed_issues:
        content.append("## Recent Closed Issues\n")
        for issue in closed_issues:
            labels = ""
            if issue.get('labels'):
                labels = f" [{', '.join([label['name'] for label in issue['labels']])}]"
            content.append(f"- **#{issue['number']}:** {issue['title']}{labels}")
            content.append(f"  - State: {issue['state']}")
            content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"\n✓ Repository information saved to '{output_file}'")
    return True


def main():
    # Repository to fetch
    owner = "ollama"
    repo = "ollama"
    
    # Save repository information to file
    save_repo_info_to_file(owner, repo, owner + "_" + repo + "_info.md")


if __name__ == "__main__":
    main()