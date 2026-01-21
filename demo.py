#!/usr/bin/env python3
"""
RLM Demo - Recursive Language Model demonstration.

This script shows how to use RLM to analyze large documents
using different backends (Anthropic API, local models, or custom callbacks).

Usage:
    # With Anthropic API (set ANTHROPIC_API_KEY env var)
    python demo.py

    # With Ollama (make sure ollama is running)
    python demo.py --backend ollama --model llama3.2

    # Verbose mode to see the iteration process
    python demo.py --verbose
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent))

from rlm import RLM, RLMResult
from rlm.backends import AnthropicBackend, OpenAICompatibleBackend, CallbackBackend


def load_sample_data() -> str:
    """Load sample data for testing."""
    sample_file = Path(__file__).parent / "sample_data" / "large_document.txt"

    if sample_file.exists():
        return sample_file.read_text()

    # Generate synthetic sample data if file doesn't exist
    print("Generating sample document...")
    return generate_sample_document()


def generate_sample_document() -> str:
    """Generate a synthetic large document for testing."""
    sections = []

    # Introduction
    sections.append("""# Technical Documentation: Authentication Systems

## Introduction

This document provides a comprehensive overview of authentication systems used in modern web applications. We will cover various authentication methods, their security considerations, and implementation best practices.

Authentication is the process of verifying the identity of a user, device, or system. It is a critical component of application security, ensuring that only authorized entities can access protected resources.
""")

    # OAuth section
    sections.append("""## OAuth 2.0 Authentication

OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on third-party services. It works by delegating user authentication to the service that hosts the user account.

### Key Components

1. **Resource Owner**: The user who authorizes access to their account
2. **Client**: The application requesting access
3. **Authorization Server**: Issues tokens after authentication
4. **Resource Server**: Hosts protected resources

### Security Considerations for OAuth

- Always use HTTPS for all OAuth communications
- Implement PKCE (Proof Key for Code Exchange) for public clients
- Validate redirect URIs strictly
- Use short-lived access tokens with refresh tokens
- Store tokens securely (never in localStorage for web apps)
- Implement token revocation mechanisms

### OAuth Flow Example

```
1. User clicks "Login with Google"
2. Redirect to Google's authorization endpoint
3. User authenticates and grants permissions
4. Google redirects back with authorization code
5. Exchange code for access token (server-side)
6. Use access token to access user data
```
""")

    # JWT section
    sections.append("""## JWT (JSON Web Tokens)

JSON Web Tokens are a compact, URL-safe means of representing claims between two parties. JWTs are commonly used for authentication and information exchange.

### JWT Structure

A JWT consists of three parts separated by dots:
- **Header**: Algorithm and token type
- **Payload**: Claims (user data)
- **Signature**: Verification hash

### Security Considerations for JWT

- Use strong signing algorithms (RS256, ES256) instead of HS256 in production
- Set appropriate expiration times (short for access tokens)
- Never store sensitive data in JWT payload (it's only base64 encoded, not encrypted)
- Validate all claims on the server side
- Implement token blacklisting for logout functionality
- Use secure HttpOnly cookies for storage

### Common JWT Vulnerabilities

1. Algorithm confusion attacks (alg=none)
2. Key injection attacks
3. Token sidejacking
4. Brute force attacks on weak secrets
""")

    # Session-based auth
    sections.append("""## Session-Based Authentication

Traditional session-based authentication stores user state on the server and uses cookies to identify sessions.

### How It Works

1. User submits credentials
2. Server validates and creates session
3. Session ID stored in database
4. Cookie sent to client with session ID
5. Subsequent requests include cookie
6. Server looks up session to identify user

### Security Considerations for Sessions

- Use secure, HttpOnly, SameSite cookies
- Regenerate session ID after login (prevent fixation)
- Implement session timeout (idle and absolute)
- Store sessions securely (Redis, database)
- Protect against CSRF with tokens
- Use secure random session ID generation

### Session vs JWT Comparison

| Aspect | Session | JWT |
|--------|---------|-----|
| Storage | Server | Client |
| Scalability | Requires shared storage | Stateless |
| Revocation | Easy | Complex |
| Size | Small cookie | Larger token |
""")

    # MFA section
    sections.append("""## Multi-Factor Authentication (MFA)

MFA requires users to provide multiple verification factors to gain access, significantly improving security.

### Authentication Factors

1. **Something you know**: Password, PIN
2. **Something you have**: Phone, hardware token
3. **Something you are**: Fingerprint, face recognition

### MFA Methods

- **TOTP**: Time-based One-Time Passwords (Google Authenticator)
- **SMS**: Text message codes (less secure)
- **Email**: Email verification codes
- **Push notifications**: Approve/deny on trusted device
- **Hardware tokens**: YubiKey, FIDO2 keys
- **Biometrics**: Fingerprint, facial recognition

### Security Considerations for MFA

- Prefer TOTP or hardware tokens over SMS
- Implement backup codes for account recovery
- Consider risk-based authentication
- Don't make MFA optional for sensitive operations
- Protect MFA enrollment process
""")

    # API Authentication
    sections.append("""## API Authentication Methods

### API Keys

Simple authentication using a secret key passed in headers or query parameters.

Security considerations:
- Rotate keys regularly
- Use different keys for different environments
- Implement rate limiting
- Log and monitor key usage
- Never expose keys in client-side code

### HTTP Basic Authentication

Base64 encoded username:password in Authorization header.

Security considerations:
- Only use over HTTPS
- Don't use for browser-based apps
- Consider for server-to-server communication

### Bearer Tokens

Token passed in Authorization header (typically JWT or opaque tokens).

Security considerations:
- Validate token on every request
- Use short expiration times
- Implement proper token storage
- Consider token binding
""")

    # Best Practices
    sections.append("""## Authentication Best Practices Summary

### Password Security
- Enforce strong password policies
- Use bcrypt, scrypt, or Argon2 for hashing
- Implement account lockout after failed attempts
- Support password managers (don't block paste)

### General Security
- Implement rate limiting
- Use HTTPS everywhere
- Log authentication events
- Monitor for anomalies
- Implement proper error handling (don't leak info)
- Keep dependencies updated

### User Experience
- Provide clear error messages (without security info)
- Support "Remember me" functionality securely
- Implement secure password reset flows
- Allow users to view active sessions

## Conclusion

Choosing the right authentication method depends on your specific requirements, including security needs, user experience goals, and technical constraints. Often, a combination of methods provides the best balance of security and usability.

Remember: Authentication is just one part of a comprehensive security strategy. Always consider authorization, data protection, and monitoring as well.
""")

    # Add some repetition to make it larger
    full_doc = "\n".join(sections)

    # Repeat sections with variations to simulate a larger document
    variations = [
        "\n\n---\n\n## Appendix A: Implementation Examples\n\n" + sections[1].replace("OAuth 2.0", "OAuth 2.0 Implementation Details"),
        "\n\n---\n\n## Appendix B: Security Checklist\n\n" + sections[2].replace("JWT", "JWT Security Checklist"),
        "\n\n---\n\n## Appendix C: Troubleshooting Guide\n\n" + sections[3].replace("Session-Based", "Session-Based Troubleshooting"),
    ]

    full_doc += "\n".join(variations)

    return full_doc


def demo_anthropic(verbose: bool = False):
    """Demo using Anthropic API."""
    print("\n" + "="*60)
    print("RLM Demo: Anthropic API Backend")
    print("="*60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
        return None

    backend = AnthropicBackend(api_key=api_key)

    # Use Sonnet for root, Haiku for recursive calls (cost-efficient)
    rlm = RLM(
        backend,
        model="claude-sonnet-4-20250514",
        recursive_model="claude-haiku-3-20250813",
        verbose=verbose,
        max_iterations=8,
    )

    return rlm


def demo_ollama(model: str = "llama3.2", verbose: bool = False):
    """Demo using Ollama local model."""
    print("\n" + "="*60)
    print(f"RLM Demo: Ollama Backend (model: {model})")
    print("="*60)

    backend = OpenAICompatibleBackend(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    rlm = RLM(
        backend,
        model=model,
        verbose=verbose,
        max_iterations=8,
    )

    return rlm


def demo_callback(verbose: bool = False):
    """Demo using a custom callback backend."""
    print("\n" + "="*60)
    print("RLM Demo: Custom Callback Backend")
    print("="*60)

    # State tracker for multi-turn mock conversation
    state = {"turn": 0}

    def mock_llm(messages: list[dict], model: str) -> str:
        """Mock LLM that demonstrates a realistic RLM flow."""
        # Check if this is a sub-LLM call (no system message = sub-call)
        has_system = any(m.get("role") == "system" for m in messages)
        if not has_system:
            # This is a sub-LLM call from llm_query
            return "Sub-LLM analysis: Found multiple security considerations including HTTPS requirements, token management, and access control patterns."

        state["turn"] += 1
        turn = state["turn"]

        # Simulate a realistic multi-turn RLM conversation
        if turn == 1:
            return """Let me start by analyzing the context.

```python
# First, check the size and structure
print(f"Context size: {len(CONTEXT):,} characters")
print(f"Number of lines: {CONTEXT.count(chr(10))}")

# Look for section headers
headers = re.findall(r'^##? .+$', CONTEXT, re.MULTILINE)
print(f"\\nFound {len(headers)} section headers:")
for h in headers[:10]:
    print(f"  - {h}")
```"""

        elif turn == 2:
            return """Good, I can see this is a technical document about authentication. Let me search for specific authentication methods.

```python
# Search for authentication-related terms
auth_terms = ['OAuth', 'JWT', 'Session', 'MFA', 'API Key', 'TOTP', 'Basic Auth']
findings = {}

for term in auth_terms:
    matches = re.findall(rf'(?i){term}[^.]*\\.', CONTEXT)
    if matches:
        findings[term] = len(matches)
        print(f"{term}: found {len(matches)} mentions")
```"""

        elif turn == 3:
            return """Now let me use the sub-LLM to analyze each authentication section in detail.

```python
# Extract the OAuth section and analyze it
oauth_match = re.search(r'## OAuth.*?(?=## |$)', CONTEXT, re.DOTALL)
if oauth_match:
    oauth_section = oauth_match.group()[:2000]  # Limit size
    oauth_analysis = llm_query(f"Extract key security considerations from:\\n{oauth_section}")
    print(f"OAuth analysis:\\n{oauth_analysis[:500]}")
```"""

        elif turn == 4:
            return """Let me compile all findings into a final answer.

```python
summary = '''
## Authentication Methods Found:

1. **OAuth 2.0**
   - Authorization framework for third-party access
   - Security: Use HTTPS, implement PKCE, validate redirect URIs, short-lived tokens

2. **JWT (JSON Web Tokens)**
   - Stateless authentication tokens
   - Security: Use RS256/ES256, short expiration, don't store sensitive data

3. **Session-Based Authentication**
   - Server-side state with cookies
   - Security: HttpOnly/SameSite cookies, regenerate session IDs, implement timeouts

4. **Multi-Factor Authentication (MFA)**
   - Multiple verification factors
   - Security: Prefer TOTP/hardware tokens over SMS, implement backup codes

5. **API Authentication**
   - API Keys, Bearer Tokens, HTTP Basic
   - Security: Rotate keys, rate limiting, HTTPS only
'''

FINAL(summary)
```"""

        # Fallback
        return """```python
FINAL("Analysis complete. See above for authentication methods and security considerations.")
```"""

    backend = CallbackBackend(mock_llm)

    rlm = RLM(
        backend,
        model="mock-model",
        verbose=verbose,
        max_iterations=8,
    )

    return rlm


def run_demo(rlm: RLM, context: str, query: str):
    """Run a demo query and display results."""
    print(f"\nQuery: {query}")
    print(f"Context size: {len(context):,} characters")
    print("\nProcessing...")

    result = rlm.completion(context, query)

    print("\n" + "-"*60)
    print("RESULT")
    print("-"*60)
    print(f"Success: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"\nAnswer:\n{result.answer}")

    print("\n" + "-"*60)
    print("STATISTICS")
    print("-"*60)
    stats = rlm.cost_summary()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return result


def main():
    parser = argparse.ArgumentParser(description="RLM Demo")
    parser.add_argument(
        "--backend",
        choices=["anthropic", "ollama", "callback"],
        default="anthropic",
        help="Backend to use (default: anthropic)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use (default depends on backend)",
    )
    parser.add_argument(
        "--query",
        default="What are all the authentication methods mentioned in this document and their key security considerations?",
        help="Query to ask",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--context-file",
        type=Path,
        help="Path to custom context file",
    )

    args = parser.parse_args()

    # Load context
    if args.context_file:
        context = args.context_file.read_text()
        print(f"Loaded context from: {args.context_file}")
    else:
        context = load_sample_data()
        # Save sample data for future use
        sample_path = Path(__file__).parent / "sample_data" / "large_document.txt"
        sample_path.parent.mkdir(exist_ok=True)
        sample_path.write_text(context)
        print(f"Sample data saved to: {sample_path}")

    # Create RLM with selected backend
    if args.backend == "anthropic":
        rlm = demo_anthropic(verbose=args.verbose)
    elif args.backend == "ollama":
        model = args.model or "llama3.2"
        rlm = demo_ollama(model=model, verbose=args.verbose)
    elif args.backend == "callback":
        rlm = demo_callback(verbose=args.verbose)

    if rlm is None:
        sys.exit(1)

    # Run the demo
    run_demo(rlm, context, args.query)


if __name__ == "__main__":
    main()
