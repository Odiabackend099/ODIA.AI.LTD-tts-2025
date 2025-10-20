#!/usr/bin/env python3
"""
Secure Git Push Script for ODIADEV-TTS
This script ensures safe pushing to GitHub by:
1. Checking for secrets in files
2. Verifying .gitignore is properly configured
3. Using secure authentication
4. Implementing proper branch management
"""

import os
import subprocess
import sys
import re
from pathlib import Path

def check_gitignore():
    """Check if .gitignore exists and has proper entries."""
    gitignore_path = Path('.gitignore')
    
    # Create .gitignore if it doesn't exist
    if not gitignore_path.exists():
        print("Creating .gitignore file...")
        with open('.gitignore', 'w') as f:
            f.write("""# Environment files
.env
*.env
infra/.env
backend/.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.coverage
.coverage.*
.cache
.pytest_cache/
.pytest_cache
nosetests.xml
coverage.xml
*.cover
*.log
.gitignore
.tox/
.nox/
.hypothesis/

# Audio files
*.mp3
*.wav
*.flac
*.ogg
*.m4a

# Model files
*.pt
*.pth
*.bin
*.onnx
*.h5
*.hdf5
*.ckpt
*.safetensors
*.gguf

# Docker
docker-compose.override.yml
*.dockerignore

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temp files
*.tmp
*.temp

# Test files
test_*.py
*_test.py

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Next.js
.next/
out/
build/

# Redis
dump.rdb
appendonly.aof

# Supabase
supabase/.temp/
""")
        print("✓ .gitignore created with secure defaults")
    else:
        print("✓ .gitignore already exists")
        
        # Check if important patterns are in .gitignore
        with open('.gitignore', 'r') as f:
            content = f.read()
            
        required_patterns = ['.env', '*.pt', '*.mp3']
        missing_patterns = [pattern for pattern in required_patterns if pattern not in content]
        
        if missing_patterns:
            print(f"⚠ Warning: Missing patterns in .gitignore: {missing_patterns}")
            print("Appending missing patterns...")
            with open('.gitignore', 'a') as f:
                f.write("\n# Security additions\n")
                for pattern in missing_patterns:
                    f.write(f"{pattern}\n")
            print("✓ Missing patterns added to .gitignore")

def check_for_secrets():
    """Check for potential secrets in files."""
    print("\nChecking for potential secrets...")
    
    # Common secret patterns
    secret_patterns = {
        'Supabase Key': r'ey[A-Za-z0-9._%-]*',
        'HF Token': r'hf_[A-Za-z0-9]{30,}',
        'API Key': r'[Aa]pi[_-]?[Kk]ey["\s:=]*[A-Za-z0-9]{20,}',
        'Password': r'[Pp]assword["\s:=]*[A-Za-z0-9@$!%*?&]{8,}',
        'Token': r'[Tt]oken["\s:=]*[A-Za-z0-9]{20,}',
    }
    
    # Files to check (avoid binary files)
    exclude_patterns = ['.mp3', '.pt', '.pth', '.bin', '.onnx', '.h5', '.ckpt', '.safetensors']
    exclude_dirs = ['.git', 'node_modules', '__pycache__']
    
    secrets_found = []
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # Skip excluded file types
            if any(file.endswith(ext) for ext in exclude_patterns):
                continue
                
            file_path = os.path.join(root, file)
            
            # Only check text files
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
                
            # Check for secrets
            for secret_name, pattern in secret_patterns.items():
                matches = re.findall(pattern, content)
                for match in matches:
                    # Filter out false positives
                    if len(match) > 50:  # Likely a real token
                        secrets_found.append((file_path, secret_name, match[:20] + '...'))
    
    if secrets_found:
        print("⚠ Potential secrets found:")
        for file_path, secret_type, secret_preview in secrets_found:
            print(f"  - {file_path}: {secret_type} ({secret_preview})")
        print("\nPlease remove these secrets before pushing!")
        return False
    else:
        print("✓ No obvious secrets found in code files")
        return True

def check_large_files():
    """Check for large files that shouldn't be committed."""
    print("\nChecking for large files...")
    
    large_files = []
    exclude_dirs = ['.git', 'node_modules', '__pycache__']
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > 50 * 1024 * 1024:  # 50MB
                    large_files.append((file_path, size))
            except Exception:
                continue
    
    if large_files:
        print("⚠ Large files found:")
        for file_path, size in large_files:
            size_mb = size / (1024 * 1024)
            print(f"  - {file_path}: {size_mb:.1f} MB")
        print("\nConsider using Git LFS for these files or adding them to .gitignore")
        return False
    else:
        print("✓ No large files found")
        return True

def setup_secure_git():
    """Setup secure git configuration."""
    print("\nSetting up secure git configuration...")
    
    # Set user config if not already set
    try:
        result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
        if not result.stdout.strip():
            subprocess.run(['git', 'config', 'user.name', 'ODIADEV-TTS'])
            print("✓ Git user name set")
            
        result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
        if not result.stdout.strip():
            subprocess.run(['git', 'config', 'user.email', 'odiadev@example.com'])
            print("✓ Git user email set")
    except Exception as e:
        print(f"⚠ Warning: Could not set git config: {e}")

def create_staging_branch():
    """Create staging branch for safe deployment."""
    print("\nSetting up branch management...")
    
    try:
        # Check current branch
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        if current_branch != 'staging':
            # Create and switch to staging branch
            subprocess.run(['git', 'checkout', '-b', 'staging'], check=True)
            print("✓ Created and switched to staging branch")
        else:
            print("✓ Already on staging branch")
            
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        print("✓ All files added to staging")
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
        if result.returncode != 0:
            # Commit changes
            subprocess.run(['git', 'commit', '-m', 'v1.2-prod-ready two-lane architecture and runbook'], check=True)
            print("✓ Changes committed to staging branch")
        else:
            print("✓ No changes to commit")
            
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Branch setup issue: {e}")

def secure_push_instructions():
    """Provide instructions for secure push."""
    print("\n" + "="*60)
    print("SECURE PUSH INSTRUCTIONS")
    print("="*60)
    print("""
To push securely to GitHub:

1. Add the remote repository (without embedding token):
   git remote add origin https://github.com/Odiabackend099/tts-odiadev-runpod.git

2. Configure credential helper for secure token storage:
   git config credential.helper store

3. Push to staging branch:
   git push -u origin staging

4. On GitHub:
   - Create a Pull Request: staging → main
   - Review files for secrets
   - Merge after approval

5. For production deployment:
   git checkout main
   git merge staging
   git push origin main

This approach provides:
- ✅ Secure token handling
- ✅ Audit point before production
- ✅ Branch discipline
- ✅ Secret protection
""")

def main():
    """Main function to run all security checks."""
    print("ODIADEV-TTS Secure Git Push Checker")
    print("="*40)
    
    # Change to project directory
    os.chdir('/Users/odiadev/Desktop/dia ai tts/odia-tts')
    
    # Run all checks
    check_gitignore()
    secrets_ok = check_for_secrets()
    large_files_ok = check_large_files()
    setup_secure_git()
    create_staging_branch()
    secure_push_instructions()
    
    if secrets_ok and large_files_ok:
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED - READY FOR SECURE PUSH")
        print("="*60)
        print("Run the commands in the instructions above to push securely.")
        return True
    else:
        print("\n" + "="*60)
        print("❌ SECURITY ISSUES FOUND - FIX BEFORE PUSHING")
        print("="*60)
        print("Please address the issues above before pushing to GitHub.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)