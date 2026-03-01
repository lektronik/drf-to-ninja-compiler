# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅ Yes             |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not open a public issue.**
2. Email the maintainer or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability).
3. Include a description of the vulnerability and steps to reproduce it.

We will acknowledge your report within 48 hours and provide an estimated timeline for a fix.

## Security Measures

This project uses:
- `bandit` for static security analysis on every commit
- `pre-commit` hooks to prevent common security issues
- No network calls or file system writes outside of explicitly specified output directories
