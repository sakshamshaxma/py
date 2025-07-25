import os
import subprocess

# Set working directory
base_dir = r"C:\Users\saksh\Downloads\Angular"
os.chdir(base_dir)

# Get list of folders
folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

for folder in folders:
    repo_name = folder
    path = os.path.join(base_dir, folder)

    print(f"\nCreating and pushing {repo_name}...")

    os.chdir(path)

    # Initialize git repo
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)

    # Create repo on GitHub using GitHub CLI
    subprocess.run([
        "gh", "repo", "create", repo_name,
        "--private", "--source=.", "--remote=origin", "--push"
    ], check=True)
