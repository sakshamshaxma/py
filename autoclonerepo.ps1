# --- Configuration ---
$GitHubUsername = "sakshamxsharma"
$GitHubToken = "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"  # Your GitHub PAT
$PerPage = 100
$Page = 1

do {
    Write-Host "Fetching page $Page..."

    # Fix: Wrap in ${} to avoid colon parsing issue
    $authHeader = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${GitHubUsername}:${GitHubToken}"))

    $headers = @{
        Authorization = $authHeader
        'User-Agent'  = 'PowerShell'
    }

    $url = "https://api.github.com/user/repos?visibility=private&affiliation=owner,collaborator&per_page=$PerPage&page=$Page"
    $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get

    if ($response.Count -eq 0) {
        break
    }

    foreach ($repo in $response) {
        $repoName = $repo.name
        $cloneUrl = $repo.clone_url

        # Embed credentials into the clone URL
        $authUrl = $cloneUrl -replace "^https://", "https://${GitHubUsername}:${GitHubToken}@"

        Write-Host "Cloning $repoName..."
        git clone $authUrl
    }

    $Page++
} while ($true)
