# Set working directory
cd "C:\Users\saksh\Downloads\Angular"

# Get list of folders
$folders = Get-ChildItem -Directory

foreach ($folder in $folders) {
    $repoName = $folder.Name
    $path = $folder.FullName

    Write-Host "`nCreating and pushing $repoName..."

    cd $path

    # Initialize git repo
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main

    # Create repo on GitHub using GitHub CLI
    gh repo create $repoName --private --source=. --remote=origin --push
}
