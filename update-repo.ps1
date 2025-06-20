<#
.SYNOPSIS
    Update and push local changes to a GitHub repository.
.DESCRIPTION
    Stages all modifications, commits with a timestamped or custom message, and pushes to the specified branch.
.PARAMETER RepoPath
    Path to the local Git repository. Default is current directory.
.PARAMETER Branch
    Name of the branch to push to. Default is 'main'.
.PARAMETER CommitMessage
    Custom commit message. Defaults to "Auto-update <timestamp>".
.EXAMPLE
    .\update-repo.ps1 -RepoPath 'C:\Projects\MyRepo' -Branch 'develop' -CommitMessage 'Sync changes'
#>
Param(
    [Parameter(Mandatory=$false)]
    [string]$RepoPath = ".",

    [Parameter(Mandatory=$false)]
    [string]$Branch = "main",

    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "Auto-update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

# Navigate to the repository
Set-Location -Path $RepoPath

# Ensure it is a Git repository
if (-not (Test-Path ".git")) {
    Write-Error "Directory '$RepoPath' is not a Git repository."
    exit 1
}

# Stage all changes
git add .

# Check if there are staged changes
# git diff-index --quiet returns 0 if no changes, 1 if there are changes
git diff-index --quiet HEAD --
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to commit."
    exit 0
}

# Commit and push
$commitResult = git commit -m "$CommitMessage"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Commit failed. Aborting Push."
    exit 1
}

$pushResult = git push "origin" "$Branch"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Push to branch '$Branch' failed."
    exit 1
}

Write-Host "Changes successfully committed and pushed to '$Branch'."
