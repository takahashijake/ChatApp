# Security Policy

ChatApp is an educational networking application and is **not designed for untrusted public
internet deployment**.

## Current security boundaries

- TCP chat traffic is plaintext; there is no TLS encryption.
- Users are identified by a chosen username; there is no authentication.
- The server exposes a deliberately small line-oriented protocol.
- Message lines are size-limited and usernames are validated to reduce malformed-input risk.
- The browser gateway uses WebSocket as a transport adapter; it does not add authentication or
  encryption to the underlying chat model.
- HTTP responses include a restrictive Content Security Policy, frame denial, MIME sniffing
  protection, and a no-referrer policy.
- The browser frontend loads no third-party JavaScript, CSS, fonts, or CDN assets.

Do not expose the TCP server or web gateway directly to an untrusted public network or use ChatApp
for sensitive conversations.

For a public deployment, add authenticated identities, TLS termination, origin restrictions,
rate limiting, abuse controls, and deployment-specific network policy first.

## Reporting a vulnerability

Please open a private GitHub security advisory for the repository when possible. Avoid publishing
working exploit details in a public issue before a fix is available.
