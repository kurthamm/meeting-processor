<#
.SYNOPSIS
    Update and push local changes to a GitHub repository.
.DESCRIPTION
    Stages all modifications, commits with a timestamped or custom message, and pushes to the specified branch.
#>
Param(
    [Parameter(Mandatory=$false)]
    [string]$RepoPath = ".",
    [Parameter(Mandatory=$false)]
    [string]$Branch = "main",
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "Auto-update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

Write-Host "Starting repository update..." -ForegroundColor Cyan
Write-Host "Repository Path: $RepoPath" -ForegroundColor Yellow
Write-Host "Branch: $Branch" -ForegroundColor Yellow
Write-Host "Commit Message: $CommitMessage" -ForegroundColor Yellow

# Navigate to the repository
Set-Location -Path $RepoPath
Write-Host "Current Location: $(Get-Location)" -ForegroundColor Gray

# Ensure it is a Git repository
if (-not (Test-Path ".git")) {
    Write-Error "Directory '$RepoPath' is not a Git repository."
    exit 1
}

# Show current branch
$currentBranch = git branch --show-current
Write-Host "Current Branch: $currentBranch" -ForegroundColor Gray

# Show status before staging
Write-Host "`nGit Status Before Staging:" -ForegroundColor Cyan
git status --short

# Stage all changes
Write-Host "`nStaging all changes..." -ForegroundColor Cyan
git add .

# Show what was staged
Write-Host "`nStaged Changes:" -ForegroundColor Cyan
git diff --staged --name-status

# Check if there are staged changes
git diff-index --quiet HEAD --
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to commit." -ForegroundColor Yellow
    exit 0
}

# Commit
Write-Host "`nCommitting changes..." -ForegroundColor Cyan
git commit -m "$CommitMessage"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Commit failed. Aborting Push."
    exit 1
}

# Push
Write-Host "`nPushing to origin/$Branch..." -ForegroundColor Cyan
git push origin $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Error "Push to branch '$Branch' failed."
    
    # Show more details about the error
    Write-Host "`nTrying to fetch latest changes..." -ForegroundColor Yellow
    git fetch origin
    
    Write-Host "`nLocal vs Remote status:" -ForegroundColor Yellow
    git status -uno
    
    exit 1
}

Write-Host "`nChanges successfully committed and pushed to '$Branch'." -ForegroundColor Green