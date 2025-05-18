#!/usr/bin/env python3
"""
Script to check for leaked secrets in the codebase.
"""

import os
import re
import sys
import subprocess
from typing import List, Tuple, Set

# Patterns to check for
PATTERNS = [
    r"DISCORD_TOKEN=[a-zA-Z0-9_\.\-]+",
    r"OPENROUTER_API_KEY=[a-zA-Z0-9_\.\-]+",
    r"SPOTIFY_CLIENT_SECRET=[a-zA-Z0-9_\.\-]+",
    r"TENOR_API_KEY=[a-zA-Z0-9_\.\-]+",
    r"OPENWEATHERMAP_API_KEY=[a-zA-Z0-9_\.\-]+",
    r"api_key\s*=\s*['\"][a-zA-Z0-9_\.\-]+['\"]",
    r"apikey\s*=\s*['\"][a-zA-Z0-9_\.\-]+['\"]",
    r"secret\s*=\s*['\"][a-zA-Z0-9_\.\-]+['\"]",
    r"password\s*=\s*['\"][a-zA-Z0-9_\.\-]+['\"]",
    r"token\s*=\s*['\"][a-zA-Z0-9_\.\-]+['\"]",
]

# Files to exclude from checking
EXCLUDED_FILES = [
    ".gitignore",
    ".env.example",
    "pre-commit",
    "README.md",
    "docs/API_SETUP.md",
    "scripts/check_secrets.py",
]

def get_all_files() -> List[str]:
    """Get all files in the repository."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.splitlines()

def check_file(file_path: str) -> List[Tuple[str, str]]:
    """Check a file for sensitive information."""
    # Skip excluded files
    for excluded in EXCLUDED_FILES:
        if excluded in file_path:
            return []
    
    # Skip if file doesn't exist
    if not os.path.exists(file_path):
        return []
    
    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return []
    
    # Check for sensitive patterns
    matches = []
    for pattern in PATTERNS:
        for match in re.finditer(pattern, content):
            matches.append((file_path, match.group(0)))
    
    return matches

def main():
    """Main function."""
    print("Checking for leaked secrets in the codebase...")
    
    # Get all files in the repository
    files = get_all_files()
    
    # Check each file
    all_matches = []
    for file_path in files:
        matches = check_file(file_path)
        all_matches.extend(matches)
    
    # Print results
    if all_matches:
        print(f"Found {len(all_matches)} potential leaked secrets:")
        for file_path, match in all_matches:
            print(f"  {file_path}: {match}")
        return 1
    else:
        print("No leaked secrets found.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
