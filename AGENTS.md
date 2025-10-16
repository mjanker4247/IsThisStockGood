# Agent Guidelines

These instructions apply to the entire repository.

## Project Overview
- The project is a Python 3.8+ Flask service with supporting data-processing utilities.
- Code is managed with Poetry; always update `pyproject.toml`/`poetry.lock` together when dependency changes are required.

## Coding Standards
- Follow PEP 8 and prefer type hints on new or modified functions.
- The repository uses two-space indentation; respect existing formatting and avoid introducing unused imports.
- Keep business logic pure and deterministic where practical, isolating I/O into helper modules.
- Do not wrap imports in try/except blocks.

## Testing & Quality
- Run the full suite with `poetry run pytest` when modifying code or tests. Skip tests only for documentation-only changes.
- Add or update tests under `tests/` to cover new functionality, including integration-style tests for Flask endpoints.
- When feasible, run `poetry run pylint isthisstockgood` and address actionable warnings.

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
