#!/bin/bash

# Security Check Script - Pre-push validation
# Prevents secrets and large files from being committed

echo "🔐 Running security check..."

# Check for secrets in staged files
SECRETS_FOUND=0

# Get list of staged files (excluding security check script)
STAGED_FILES=$(git diff --cached --name-only | grep -v "scripts/security_check.sh")

# If no staged files, skip secret check
if [ -z "$STAGED_FILES" ]; then
    echo "✅ No staged files to check"
else
    # Check for common secret patterns
    PATTERNS=(
        "ghp_[A-Za-z0-9_]{36}"
        "gho_[A-Za-z0-9_]{36}"
        "ghu_[A-Za-z0-9_]{36}"
        "ghs_[A-Za-z0-9_]{36}"
        "ghr_[A-Za-z0-9_]{36}"
        "SUPABASE.*KEY"
        "REDIS.*URL"
        "HF_TOKEN"
        "API_KEY"
        "SECRET_KEY"
        "PRIVATE_KEY"
        "-----BEGIN.*PRIVATE KEY-----"
    )

    for pattern in "${PATTERNS[@]}"; do
        if echo "$STAGED_FILES" | xargs grep -l -E "$pattern" 2>/dev/null; then
            echo "❌ SECRET DETECTED: Pattern '$pattern' found in staged files"
            SECRETS_FOUND=1
        fi
    done
fi

# Check for large files (>50MB)
LARGE_FILES=$(git diff --cached --name-only | xargs ls -la 2>/dev/null | awk '$5 > 52428800 {print $9 " (" $5 " bytes)"}')
if [ ! -z "$LARGE_FILES" ]; then
    echo "❌ LARGE FILES DETECTED:"
    echo "$LARGE_FILES"
    SECRETS_FOUND=1
fi

# Check for sensitive file types
SENSITIVE_FILES=$(git diff --cached --name-only | grep -E "\.(env|key|pem|pt|mp3|wav)$")
if [ ! -z "$SENSITIVE_FILES" ]; then
    echo "❌ SENSITIVE FILES DETECTED:"
    echo "$SENSITIVE_FILES"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 1 ]; then
    echo ""
    echo "🚨 SECURITY VIOLATION DETECTED!"
    echo "Please remove secrets and sensitive files before pushing."
    echo ""
    echo "To fix:"
    echo "1. git reset HEAD <file>  # Unstage sensitive files"
    echo "2. Add to .gitignore"
    echo "3. Re-commit without secrets"
    exit 1
fi

echo "✅ No secrets detected"
echo "✅ No large files detected"
echo "✅ Security check passed"
exit 0
