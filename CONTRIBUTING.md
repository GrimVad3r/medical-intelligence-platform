# Contributing – Medical Intelligence Platform

## Development setup

1. Fork and clone the repo.
2. Run `./scripts/setup.sh` (or `setup.ps1` on Windows).
3. Install pre-commit: `pre-commit install`.
4. Create a branch: `git checkout -b feature/your-feature`.

## Code style

- **Formatter:** Black (see `black.toml`).
- **Import sort:** isort (see `isort.cfg`).
- **Linting:** Flake8 (`.flake8`), Pylint (`.pylintrc`).
- **Types:** mypy (`.mypy.ini`).

```bash
make lint
make format
```

## Tests

```bash
pytest
pytest tests/unit
pytest tests/integration -v
```

- Unit tests in `tests/unit/`.
- Integration in `tests/integration/`.
- Fixtures in `tests/conftest.py` and `tests/fixtures/`.

## Pull requests

1. Ensure tests pass and lint is clean.
2. Update docs if you change behavior or add options.
3. Keep PRs focused; reference issues where applicable.

## Documentation

- Docstrings for public functions and classes.
- Update README, ARCHITECTURE, INSTALLATION, and API_REFERENCE as needed.
