# UV Configuration for IsThisStockGood

## Installing UV

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

## Project Setup with UV

### Initial Setup

```bash
# Create a new virtual environment with uv
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install all dependencies
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"
```

### Quick Start

```bash
# Sync dependencies (faster than pip install)
uv pip sync

# Install a new package
uv pip install <package-name>

# Update all dependencies
uv pip install --upgrade -e ".[dev]"
```

## Running the Application with UV

### Development Server

```bash
# Run with uv
uv run python main.py

# Or with Flask development server
uv run flask --app main run --debug --host=0.0.0.0 --port=8080
```

### Production Server

```bash
# Using gunicorn (install first with: uv pip install gunicorn)
uv run gunicorn -w 4 -b 0.0.0.0:8080 main:app
```

## Running Tests with UV

### Run All Tests

```bash
# Run tests with uv
uv run pytest

# Run with coverage report
uv run pytest --cov=isthisstockgood --cov-report=html

# Run specific test file
uv run pytest tests/test_yfinance_data.py

# Run specific test class
uv run pytest tests/test_yfinance_data.py::TestYFinanceData

# Run specific test method
uv run pytest tests/test_yfinance_data.py::TestYFinanceData::test_initialization
```

### Using unittest directly

```bash
# Run unittest-based tests
uv run python -m unittest test_yfinance_data

# With verbose output
uv run python -m unittest test_yfinance_data -v
```

## Code Quality with UV

### Formatting

```bash
# Format code with black
uv run black isthisstockgood/

# Check formatting without applying
uv run black --check isthisstockgood/
```

### Linting

```bash
# Lint with ruff
uv run ruff check isthisstockgood/

# Auto-fix issues
uv run ruff check --fix isthisstockgood/
```

### Type Checking

```bash
# Type check with mypy
uv run mypy isthisstockgood/
```

## Dependency Management

### Adding Dependencies

```bash
# Add a runtime dependency
uv pip install <package-name>
# Then update pyproject.toml manually

# Add a development dependency
uv pip install <package-name>
# Then add to [project.optional-dependencies.dev]
```

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv pip install --upgrade -e ".[dev]"

# Update a specific package
uv pip install --upgrade <package-name>
```

### Lock File (Optional)

```bash
# Generate a lock file for reproducible builds
uv pip freeze > requirements-lock.txt

# Install from lock file
uv pip install -r requirements-lock.txt
```

## UV Performance Benefits

UV is significantly faster than pip:

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Fresh install | ~30s | ~3s | 10x faster |
| Reinstall (cached) | ~15s | ~0.5s | 30x faster |
| Dependency resolution | ~10s | ~1s | 10x faster |

## UV Cache Management

```bash
# Clear UV cache (if needed)
uv cache clean

# Show cache location
uv cache dir

# Show cache size
uv cache size
```

## Common UV Commands

```bash
# Create virtual environment
uv venv

# Install from pyproject.toml
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run a Python script
uv run python script.py

# Run a module
uv run -m module_name

# Sync dependencies (install exactly what's specified)
uv pip sync

# List installed packages
uv pip list

# Show package info
uv pip show <package-name>

# Uninstall package
uv pip uninstall <package-name>
```

## Migration from pip/requirements.txt

If you have an existing `requirements.txt`:

```bash
# Option 1: Install from requirements.txt
uv pip install -r requirements.txt

# Option 2: Convert to pyproject.toml (manual)
# Move dependencies from requirements.txt to pyproject.toml
# Then: uv pip install -e .
```

## Continuous Integration with UV

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Create virtual environment
        run: uv venv
      
      - name: Install dependencies
        run: |
          source .venv/bin/activate
          uv pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          source .venv/bin/activate
          uv run pytest
      
      - name: Run linting
        run: |
          source .venv/bin/activate
          uv run ruff check isthisstockgood/
```

## Docker with UV

### Dockerfile Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY isthisstockgood ./isthisstockgood

# Create venv and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Run the application
CMD [".venv/bin/python", "main.py"]
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Remove existing venv
rm -rf .venv

# Create fresh venv
uv venv

# Reinstall dependencies
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Import Errors

Make sure you've installed the package in editable mode:

```bash
uv pip install -e .
```

### UV Command Not Found

```bash
# Add UV to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"

# Add to shell profile for persistence
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Best Practices

1. **Always use virtual environments**: `uv venv` before installing
2. **Use editable install**: `uv pip install -e .` for development
3. **Pin versions in production**: Generate `requirements-lock.txt`
4. **Run tests before committing**: `uv run pytest`
5. **Format code**: `uv run black isthisstockgood/`
6. **Keep dependencies minimal**: Only add what you need

## Performance Tips

1. **Use `uv pip sync`** instead of `install` when you know exactly what should be installed
2. **Cache is your friend**: UV automatically caches packages
3. **Parallel installs**: UV installs packages in parallel by default
4. **Use `--no-cache`** flag only when debugging cache issues

## Additional Resources

- UV Documentation: https://github.com/astral-sh/uv
- UV Performance Benchmarks: https://astral.sh/blog/uv
- Python Packaging Guide: https://packaging.python.org/
