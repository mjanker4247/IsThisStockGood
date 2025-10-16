# Agent Guidelines

These instructions apply to the entire repository.

## Project Overview
- The project is a Python 3.8+ Flask service with data-processing utilities.
- Dependencies are managed with **uv**. When dependency changes are required, update `pyproject.toml` and regenerate the lock data via `uv lock`.

## Coding Standards
- Follow PEP 8 and prefer type hints on new or modified functions.
- Use four-space indentation in Python files and avoid introducing unused imports.
- Keep business logic pure and deterministic when practical, isolating I/O into helper modules.
- Do not wrap imports in `try`/`except` blocks.

## Testing & Quality
- Run the full suite with `uv run pytest` whenever code or tests change. Skip tests only for documentation-only updates.
- Add or update tests under `tests/` to cover new functionality, including integration-style tests for Flask endpoints.
- When feasible, run `uv run pylint isthisstockgood` and address actionable warnings.

## Documentation
- Update README files, inline comments, or docstrings when behavior or configuration changes.
- Keep comments concise, accurate, and aligned with the implementation.

## Git & Review Process
- Keep commits focused with descriptive messages summarizing the change.
- Surface security-relevant changes and mitigation steps in commit/PR descriptions.
- Ensure the working tree is clean before finishing your task.

## Operational Notes
- Avoid committing secrets or credentials; rely on configuration or environment variables.
- Prefer incremental, well-tested changes that maintain compatibility with existing CLI scripts and HTTP handlers.
