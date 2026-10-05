# Contributing

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Quality checks

Run the same checks used by CI before opening a pull request:

```bash
ruff check .
pytest
python -m build
```

Use `ruff format .` to apply automatic formatting.

## Development guidelines

- Keep the wire protocol newline-delimited and UTF-8.
- Do not mutate the client registry without holding the server registry lock.
- Keep terminal UI concerns out of the socket/protocol layer where possible.
- Add or update tests for protocol, lifecycle, concurrency, or command behavior.
- Avoid broad `except:` blocks; handle expected socket failures explicitly.
- Keep changes small enough that failures can be isolated during review.

## Pull requests

Explain what changed, how it was verified, and any concurrency or compatibility risk. CI must pass
before merging.
