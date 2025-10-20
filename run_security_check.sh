#!/bin/bash
# Simple security check script

echo "ODIADEV-TTS Security Check"
echo "========================="

echo "1. Creating .gitignore if needed..."
cat > .gitignore << 'EOF'
# Environment files
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
EOF

echo "✓ .gitignore created/updated"

echo "2. Checking for large files..."
find . -type f -size +50M ! -path "./.git/*" ! -path "./node_modules/*" 2>/dev/null

echo "3. Setting up git configuration..."
git config user.name "ODIADEV-TTS"
git config user.email "odiadev@example.com"

echo "4. Creating staging branch..."
git checkout -b staging 2>/dev/null || git checkout staging

echo "5. Adding files..."
git add .

echo ""
echo "SECURE PUSH INSTRUCTIONS:"
echo "========================"
echo "1. Add remote (without token in URL):"
echo "   git remote add origin https://github.com/Odiabackend099/tts-odiadev-runpod.git"
echo ""
echo "2. Configure credential helper:"
echo "   git config credential.helper store"
echo ""
echo "3. Push to staging:"
echo "   git push -u origin staging"
echo ""
echo "4. Create PR on GitHub: staging → main"