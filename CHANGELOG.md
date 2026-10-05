# Changelog

All notable changes to ChatApp are documented here.

The project follows a lightweight form of Keep a Changelog and uses semantic version tags for
release automation.

## [Unreleased]

### Added
- Installable `chatapp` package with `chatapp-server` and `chatapp-client` console commands.
- Automated tests for protocol parsing, admin commands, username collisions, and TCP lifecycle.
- GitHub Actions CI across Python 3.11, 3.12, and 3.13.
- Tag-driven GitHub release workflow.
- Dependabot, contribution guidance, architecture documentation, and issue/PR templates.

### Changed
- Replaced module-level shared server state with an encapsulated `ChatServer`.
- Added explicit protocol and username validation.
- Made server shutdown and user kicking deterministic and idempotent.
- Preserved `python server.py` and `python client.py` compatibility entry points.

### Removed
- Tracked Python bytecode caches.
