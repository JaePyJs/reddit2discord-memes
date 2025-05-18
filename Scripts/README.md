# Utility Scripts

This directory contains utility scripts for managing and maintaining the codebase.

## Security Scripts

### check_secrets.py

This script checks the codebase for leaked secrets such as API keys, tokens, and passwords.

#### Usage

```bash
python scripts/check_secrets.py
```

#### What it checks for

- Discord tokens
- OpenRouter API keys
- Spotify client secrets
- Tenor API keys
- OpenWeatherMap API keys
- Generic API keys, tokens, passwords, and secrets

#### Configuration

You can modify the script to add more patterns to check for or exclude additional files from checking.

## Git Hooks

### pre-commit

A pre-commit hook is included in the repository to prevent committing sensitive information. To install it, run:

```bash
cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or use the pre-commit hook provided in the repository:

```bash
cp scripts/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

## Adding New Scripts

When adding new scripts to this directory:

1. Make sure they are well-documented with comments
2. Add a description to this README.md file
3. Make them executable with `chmod +x script_name.py`
4. Follow the security best practices in the SECURITY.md document
