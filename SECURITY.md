# Security Policy

## Overview

This repository contains an **educational, historically accurate simulation** of the Enigma machine cipher. It is intended for learning, historical research, and recreational purposes only.

**Important:** This simulator implements authentic Enigma cryptography for educational demonstration. It is **not intended for protecting sensitive information**. Modern cryptographic systems should be used for real-world security needs.

## Supported Versions

We maintain security patches for:

| Version | Supported |
|---------|-----------|
| latest  | ✅        |

## Security Considerations

### What This Project Is

- ✅ A historically accurate educational tool for understanding the Enigma cipher
- ✅ A working implementation of WWII-era encryption mechanism
- ✅ Suitable for learning cryptography fundamentals and historical context
- ✅ Free and open-source for research purposes

### What This Project Is NOT

- ❌ A secure encryption system for protecting sensitive data
- ❌ Suitable for real-world cryptographic applications
- ❌ A replacement for modern encryption standards (AES, RSA, etc.)
- ❌ Intended for preventing unauthorized access to private information

### Cryptographic Limitations

The Enigma cipher has well-documented mathematical weaknesses, including:

- Limited keyspace compared to modern encryption
- Rotor stepping patterns that create exploitable patterns
- Vulnerability to differential and statistical cryptanalysis
- No authentication or integrity checking mechanisms

These weaknesses are **intentional and historically accurate** to the original design. They do not represent flaws in this simulator's implementation.

## Reporting Security Issues

If you discover a **vulnerability in this simulator's code** (e.g., a bug in rotor wiring, incorrect cryptographic implementation, or a software defect), please report it responsibly:

1. **Do not open a public issue** for security vulnerabilities
2. **Submit** a report via GitHub's private security vulnerability disclosure form
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will acknowledge receipt and respond on a best-effort basis, typically within 7 days.

### What We Will Address

- Bugs in cipher implementation (incorrect wiring, rotor stepping, etc.)
- Software vulnerabilities (code injection, memory issues, etc.)
- Dependency vulnerabilities affecting the simulator

### What Is Out of Scope

- General academic critiques of Enigma weakness (these are historical facts)
- Requests to "improve" Enigma security (defeating the educational purpose)
- Suggestions to add modern cryptography (outside project scope)

## Dependencies & Vulnerabilities

This project depends on:

- **Python 3.10+** — See [python.org/security](https://www.python.org/downloads/security/)
- **Pygame** — See [pygame.org](https://www.pygame.org/)

To check for dependency vulnerabilities, you can use `pip-audit` (an external security auditing tool):

```bash
# Install pip-audit
pip install pip-audit

# Audit dependencies
pip-audit
```

**Note:** `pip-audit` is not included as a project dependency; it is an optional external tool for vulnerability scanning.
