# Security Policy

## Reporting a Vulnerability

**Please do not disclose security vulnerabilities publicly.**

If you discover a security issue in BridgeBase SDK, please report it privately by emailing:

**security@bridgebase.dev**

### What to Include

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 5 business days
- **Fix Timeline:** Depends on severity; critical issues prioritized

We appreciate responsible disclosure and will acknowledge your contribution once the issue is resolved.

## Supported Versions

Security updates are provided for the latest stable release. We recommend always using the most recent version.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Best Practices

When using this SDK:

- **Never commit JWT tokens** to version control
- **Rotate tokens regularly** according to your security policy
- **Keep dependencies updated** via `pip install --upgrade bridgebase`

Thank you for helping keep BridgeBase secure.
