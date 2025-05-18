# Security Best Practices

This document outlines security best practices for working with this codebase, particularly regarding API keys and sensitive information.

## API Keys and Tokens

### Storage

- **NEVER commit API keys, tokens, or other sensitive information to the repository**
- Store sensitive information in environment variables or `.env` files
- The `.env` file is included in `.gitignore` to prevent accidental commits
- Use `.env.example` as a template for required environment variables, but never include actual values

### Management

- Rotate API keys and tokens regularly
- Use different API keys for development and production environments
- Limit API key permissions to only what is necessary
- Monitor API key usage for unusual activity

## Git Security

### Pre-commit Hook

A pre-commit hook is included to check for sensitive information before committing:

```bash
.git/hooks/pre-commit
```

This hook checks for patterns that might indicate sensitive information and prevents the commit if any are found.

### Checking for Leaked Secrets

Use the included script to check for leaked secrets in the codebase:

```bash
python scripts/check_secrets.py
```

### Removing Sensitive Information from Git History

If sensitive information has been committed to the repository, follow these steps to remove it:

1. Install `git-filter-repo`:
   ```bash
   pip install git-filter-repo
   ```

2. Create a file with patterns to replace:
   ```bash
   echo "YOUR_API_KEY=REDACTED_API_KEY" > expressions.txt
   ```

3. Run `git-filter-repo` to replace the sensitive information:
   ```bash
   git filter-repo --replace-text expressions.txt
   ```

4. Force push the changes to the remote repository:
   ```bash
   git push --force
   ```

5. Notify all collaborators to clone a fresh copy of the repository

## Environment Variables

### Local Development

For local development, use a `.env` file with the following format:

```
DISCORD_TOKEN=your_discord_token
OPENROUTER_API_KEY=your_openrouter_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
TENOR_API_KEY=your_tenor_api_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
```

### Production

For production environments:

- Use the platform's built-in environment variable management
- Do not use `.env` files in production
- Set environment variables through the platform's dashboard or CLI

## Code Security

### Input Validation

- Validate all user input before processing
- Use parameterized queries for database operations
- Sanitize user input before displaying it

### Error Handling

- Do not expose sensitive information in error messages
- Log errors securely without including sensitive information
- Use appropriate error codes and messages for different types of errors

### Dependencies

- Keep dependencies up to date
- Regularly check for security vulnerabilities in dependencies
- Use a dependency scanning tool like `safety` or GitHub's Dependabot

## Reporting Security Issues

If you discover a security vulnerability, please report it by:

1. **DO NOT** create a public GitHub issue
2. Contact the maintainers directly through private channels
3. Provide detailed information about the vulnerability and how to reproduce it

## Additional Resources

- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
