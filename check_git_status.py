#!/usr/bin/env python3
import subprocess
import os

# Change to the project directory
os.chdir('/Users/odiadev/Desktop/dia ai tts/odia-tts')

try:
    # Check git status
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    print("Git Status:")
    print(result.stdout)
    
    # Check if there's a .gitignore file
    if os.path.exists('.gitignore'):
        print("\n.gitignore contents:")
        with open('.gitignore', 'r') as f:
            print(f.read())
    else:
        print("\nNo .gitignore file found")
        
    # Check remote URLs
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    print("\nRemote URLs:")
    print(result.stdout)
    
except Exception as e:
    print(f"Error: {e}")