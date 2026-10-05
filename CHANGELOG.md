# Changelog

All notable changes to ChatApp are documented here.

The project follows a lightweight form of Keep a Changelog and uses semantic version tags for
release automation.

## [Unreleased]

### Added
- Responsive browser frontend with desktop and mobile layouts.
- FastAPI WebSocket gateway that bridges browser sessions into the existing TCP chat server.
- `chatapp-app` combined launcher for the complete TCP + web product.
- `chatapp-web` standalone browser gateway command.
- Web frontend architecture and protocol documentation.
- End-to-end test proving messages cross between WebSocket and raw TCP clients.
- Browser response security headers.
- Installable `chatapp` package with `chatapp-server` and `chatapp-client` console commands.
- Automated tests for protocol parsing, admin commands, username collisions, and TCP lifecycle.
- GitHub Actions CI across Python 3.11, 3.12, and 3.13.
- Tag-driven GitHub release workflow.
- Dependabot, contribution guidance, architecture documentation, and issue/PR templates.

### Changed
- Package version advanced to 0.2.0 for the web frontend milestone.
- Outgoing protocol lines now enforce the same encoded size limit as incoming lines.
- Replaced module-level shared server state with an encapsulated `ChatServer`.
- Added explicit protocol and username validation.
- Made server shutdown and user kicking deterministic and idempotent.
- Preserved `python server.py` and `python client.py` compatibility entry points.

### Removed
- Tracked Python bytecode caches.
