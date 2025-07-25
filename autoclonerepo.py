import requests
import base64
import os

# --- Configuration ---
GITHUB_USERNAME = "sakshamxsharma"
GITHUB_TOKEN = "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"
PER_PAGE = 100
page = 1

while True:
    print(f"Fetching page {page}...")

    url = f"https://api.github.com/user/repos?visibility=private&affiliation=owner,collaborator&per_page={PER_PAGE}&page={page}"
    auth = (GITHUB_USERNAME, GITHUB_TOKEN)
    headers = {
        "User-Agent": "Python"
    }
    response = requests.get(url, auth=auth, headers=headers)
    repos = response.json()

    if not repos:
        break

    for repo in repos:
        repo_name = repo["name"]
        clone_url = repo["clone_url"]
        # Embed credentials into the clone URL
        auth_url = clone_url.replace(
            "https://", f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@"
        )
        print(f"Cloning {repo_name}...")
        os.system(f'git clone "{auth_url}"')

    page += 1
