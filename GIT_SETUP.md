# Git Setup Instructions

## Install Git for Windows

### Option 1: Using winget (Windows Package Manager)

```powershell
winget install --id Git.Git -e --source winget
```

### Option 2: Download Installer

1. Visit: <https://git-scm.com/download/win>
2. Download Git for Windows
3. Run installer with default settings
4. Restart PowerShell after installation

## After Installation

Run these commands in PowerShell:

```powershell
# Initialize repository
cd c:\Users\marin\Desktop\Draft_Analyzer_Project
git init

# Configure Git (use your details)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Create initial commit
git add .
git commit -m "Initial commit: Draft Analyzer project structure"
```

## Recommended Workflow

After making changes:

```powershell
# Check what changed
git status

# See file differences
git diff

# Stage and commit
git add .
git commit -m "Descriptive message about what you changed"

# View commit history
git log --oneline
```

## Useful Commands

```powershell
# Restore a file to last committed version
git checkout HEAD -- path/to/file.py

# View file at specific commit
git show commit_hash:path/to/file.py

# Create a branch for experiments
git checkout -b experiment-branch
```
