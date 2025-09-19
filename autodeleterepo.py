import requests
from getpass import getpass

# Replace with your GitHub username and personal access token
GITHUB_USER = 'your-username'
GITHUB_TOKEN = 'your-token'

# GitHub API to list repositories
repos_url = 'https://api.github.com/user/repos?per_page=1000'

# Fetch list of repositories
response = requests.get(repos_url, auth=(GITHUB_USER, GITHUB_TOKEN))

if response.status_code != 200:
    print(f"Error fetching repositories: {response.status_code}")
    exit()

repos = response.json()

# Loop through each repository
for repo in repos:
    repo_name = repo['full_name']
    
    # Ask for confirmation before deleting
    user_input = input(f"Do you want to delete the repository '{repo_name}'? (y/n): ").strip().lower()
    
    if user_input == 'y':
        # Proceed to delete the repo
        delete_url = f"https://api.github.com/repos/{repo_name}"
        delete_response = requests.delete(delete_url, auth=(GITHUB_USER, GITHUB_TOKEN))
        
        if delete_response.status_code == 204:
            print(f"Repository '{repo_name}' deleted successfully.")
        else:
            print(f"Failed to delete '{repo_name}'. Status code: {delete_response.status_code}")
    else:
        print(f"Skipping repository '{repo_name}'.")

print("Process complete.")
