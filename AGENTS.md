# Agent Instructions

These guidelines apply to the entire repository.

## Project Overview
- The codebase is a Python 3.8+ Flask service with supporting data-processing utilities.
- Prefer incremental, well-tested changes that keep existing CLI scripts and HTTP handlers functional.

## Coding Standards
- Follow PEP 8 conventions and Python typing best practices where practical; honor repository-specific pylint settings (2-space indentation, disabled message categories).
- Keep business logic pure and side-effect free when possible; isolate I/O (HTTP, file, network) to dedicated helper modules.
- Maintain compatibility with the configured dependencies in `pyproject.toml` and avoid introducing new packages without necessity.

## Testing & Quality
- Always run the full unit test suite: `poetry run pytest`.
- Add or update tests alongside code changes that affect functionality.
- For Flask endpoints, include integration-style tests under `tests/` when altering request/response behavior.
- Run `poetry run pylint isthisstockgood` and address warnings that fall outside the disabled categories.

## Documentation
- Update README or module docstrings when behavior or usage changes.
- Keep comments concise, actionable, and up to date with the implementation.

## Git & Review
- Keep commits focused; include descriptive messages summarizing the change.
- Highlight any security-sensitive modifications and document mitigation steps in the PR description.
