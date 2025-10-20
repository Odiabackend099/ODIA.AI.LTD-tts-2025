#!/bin/bash
# Comprehensive script to push ODIADEV-TTS to GitHub

echo "=== ODIADEV-TTS GitHub Push Script ==="
echo "Current directory: $(pwd)"
echo "Date: $(date)"

# Check if we're already in a git repository
if [ -d ".git" ]; then
    echo "✓ Git repository already exists"
else
    echo "Initializing new git repository..."
    git init
fi

# Check if remote already exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "✓ Remote 'origin' already exists"
    echo "Remote URL: $(git remote get-url origin)"
else
    echo "Adding remote repository..."
    git remote add origin https://github.com/Odiabackend099/tts-odiadev-runpod.git
fi

# Configure git user (if not already configured)
if [ -z "$(git config user.name)" ]; then
    echo "Setting git user configuration..."
    git config user.name "ODIADEV-TTS"
    git config user.email "odiadev@example.com"
fi

# Add all files
echo "Adding all files to git..."
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes to commit"
else
    echo "Creating commit..."
    git commit -m "ODIADEV-TTS v1.2-prod-ready: Two-lane deployment with enhanced production runbook
    
    Features:
    - Two-lane deployment (Priority/Free)
    - Enhanced production runbook
    - Demo page with marketing content
    - One-pager marketing document
    - Two-lane validation scripts
    - Watermarking enforcement
    - Cache key integrity
    - Back-pressure management
    - Storage lifecycle policies"
fi

# Fetch and merge any remote changes
echo "Fetching remote changes..."
git fetch origin

# Try to push to main branch first, then master if main doesn't exist
echo "Pushing to GitHub (main branch)..."
if git push -u origin main; then
    echo "✓ Successfully pushed to main branch"
else
    echo "Trying to push to master branch..."
    if git push -u origin master; then
        echo "✓ Successfully pushed to master branch"
    else
        echo "✗ Failed to push to both main and master branches"
        echo "Please check your GitHub repository and permissions"
        exit 1
    fi
fi

echo ""
echo "=== Push Complete ==="
echo "Repository URL: https://github.com/Odiabackend099/tts-odiadev-runpod"
echo "Commit: $(git rev-parse HEAD)"
echo "Date: $(date)"