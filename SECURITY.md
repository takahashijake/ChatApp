# Security Policy

ChatApp is an educational TCP chat application and is **not designed for untrusted public
internet deployment**.

## Current security boundaries

- Traffic is plaintext TCP; there is no TLS encryption.
- Users are identified by a chosen username; there is no authentication.
- The server intentionally exposes only a small line-oriented protocol.
- Message lines are size-limited and usernames are validated to reduce malformed-input risk.

Do not expose the server directly to the public internet or use it for sensitive conversations.

## Reporting a vulnerability

Please open a private GitHub security advisory for the repository when possible. Avoid publishing
working exploit details in a public issue before a fix is available.
