#!/bin/bash
# Script to initialize git repository and push to GitHub

echo "Initializing git repository..."
git init

echo "Adding all files..."
git add .

echo "Creating initial commit..."
git commit -m "Initial commit: ODIADEV-TTS with two-lane deployment"

echo "Adding remote repository..."
git remote add origin https://github.com/Odiabackend099/tts-odiadev-runpod.git

echo "Pushing to GitHub..."
git push -u origin main

echo "Done!"