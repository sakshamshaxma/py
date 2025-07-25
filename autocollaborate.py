import requests

<<<<<<< HEAD
GITHUB_USERNAME = "sakshamxsharma"
TOKEN = "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"
COLLABORATOR = "copilot-chat"

=======
# Replace with your GitHub username, token, and collaborator username

GITHUB_USERNAME = "sakshamxsharma"

TOKEN = "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"

COLLABORATOR = "copilot-chat"

# API endpoint to list repositories
REPO_LIST_URL = f"https://api.github.com/user/repos"

# Headers for authentication
>>>>>>> 96da162d62b899d8c129d5f3fc08b5b4b3467bb5
headers = {
    "Authorization": f"token {TOKEN}"
}

def add_collaborator(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/collaborators/{COLLABORATOR}"
    response = requests.put(url, headers=headers)
<<<<<<< HEAD
    if response.status_code == 201 or response.status_code == 204:
=======
    if response.status_code == 201:
>>>>>>> 96da162d62b899d8c129d5f3fc08b5b4b3467bb5
        print(f"Collaborator added to {repo_name}")
    else:
        print(f"Failed to add collaborator to {repo_name}: {response.status_code}")

<<<<<<< HEAD
def get_all_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch repositories: {response.status_code}")
            break
        page_repos = response.json()
        if not page_repos:
            break
        repos.extend(page_repos)
        page += 1
    return repos

repos = get_all_repos()
for repo in repos:
    add_collaborator(repo["name"])
=======
# Get the list of repositories
response = requests.get(REPO_LIST_URL, headers=headers)
if response.status_code == 200:
    repos = response.json()
    for repo in repos:
        add_collaborator(repo["name"])
else:
    print(f"Failed to fetch repositories: {response.status_code}")
>>>>>>> 96da162d62b899d8c129d5f3fc08b5b4b3467bb5
