# Fixing ModuleNotFoundError - Complete Setup Guide

## Problem

When running tests from the `tests/` folder, you get `ModuleNotFoundError` because Python can't find the `isthisstockgood` package.

## Project Structure Required

```
your-project-root/
├── isthisstockgood/           # Main package folder
│   ├── __init__.py            # Makes this a Python package (REQUIRED)
│   ├── YFinanceData.py
│   ├── DataFetcher.py
│   ├── RuleOneInvestingCalculations.py
│   ├── CompanyInfo.py
│   └── server.py
├── tests/                     # Test folder
│   ├── __init__.py            # Makes this a Python package (REQUIRED)
│   └── test_yfinance_data.py
├── main.py                    # Application entry point
├── pyproject.toml             # Package configuration
└── README.md
```

## Solution Steps

### Step 1: Create `__init__.py` Files

**Create `isthisstockgood/__init__.py`:**
```python
# isthisstockgood/__init__.py

"""
IsThisStockGood - Stock Analysis with Rule #1 Investing
"""

__version__ = "2.0.0"
```

**Create `tests/__init__.py`:**
```python
# tests/__init__.py

"""
Test suite for IsThisStockGood application
"""
```

### Step 2: Install Package in Editable Mode

This is the **key step** that fixes the import issue:

```bash
# From your project root directory (where pyproject.toml is located)
uv pip install -e .
```

The `-e` flag installs the package in "editable" mode, which means:
- Python can find your `isthisstockgood` module from anywhere
- Changes to your code are immediately available (no reinstall needed)
- Tests can import from `isthisstockgood` package

### Step 3: Verify Installation

```bash
# Check if package is installed
uv pip list | grep isthisstockgood

# Or with Python
uv run python -c "import isthisstockgood; print(isthisstockgood.__version__)"
```

Expected output: `2.0.0`

### Step 4: Run Tests

Now you can run tests from any directory:

```bash
# From project root
uv run pytest tests/

# Or with unittest
uv run python -m unittest discover tests/

# Or run specific test file
uv run python tests/test_yfinance_data.py
```

## Running Tests - Multiple Methods

### Method 1: Using pytest (Recommended)

```bash
# Install pytest if not already installed
uv pip install pytest pytest-cov

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_yfinance_data.py

# Run with coverage
uv run pytest --cov=isthisstockgood
```

### Method 2: Using unittest

```bash
# From project root
uv run python -m unittest discover tests/

# Run specific test file
uv run python -m unittest tests.test_yfinance_data

# With verbose output
uv run python -m unittest tests.test_yfinance_data -v
```

### Method 3: Direct execution

```bash
# From project root
uv run python tests/test_yfinance_data.py
```

## Common Issues and Solutions

### Issue 1: ModuleNotFoundError: No module named 'isthisstockgood'

**Solution:**
```bash
# Install package in editable mode
uv pip install -e .

# Verify installation
uv run python -c "import isthisstockgood"
```

### Issue 2: `__init__.py` missing

**Solution:**
```bash
# Create the file in isthisstockgood/ folder
touch isthisstockgood/__init__.py

# Add minimal content
echo '__version__ = "2.0.0"' > isthisstockgood/__init__.py
```

### Issue 3: Wrong directory structure

**Check your structure:**
```bash
# From project root
tree -L 2 -I '__pycache__|.venv|*.pyc'
```

**Should see:**
```
.
├── isthisstockgood/
│   ├── __init__.py
│   ├── YFinanceData.py
│   └── ...
├── tests/
│   ├── __init__.py
│   └── test_yfinance_data.py
├── main.py
└── pyproject.toml
```

### Issue 4: Virtual environment not activated

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Or use uv run (automatically uses venv)
uv run pytest
```

### Issue 5: ImportError in test file

**Update test imports:**
```python
# ❌ Wrong - won't work
import sys
sys.path.insert(0, '../isthisstockgood')
from YFinanceData import YFinanceData

# ✅ Correct - works after pip install -e .
from isthisstockgood.YFinanceData import YFinanceData
from isthisstockgood.DataFetcher import fetchDataForTickerSymbol
```

## pyproject.toml Configuration

Ensure your `pyproject.toml` has the correct package configuration:

```toml
[project]
name = "isthisstockgood"
version = "2.0.0"
# ... other settings ...

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## Quick Setup Checklist

- [ ] Project structure has `isthisstockgood/` folder
- [ ] `isthisstockgood/__init__.py` exists
- [ ] `tests/__init__.py` exists
- [ ] `pyproject.toml` exists in project root
- [ ] Virtual environment created: `uv venv`
- [ ] Virtual environment activated (or using `uv run`)
- [ ] Package installed: `uv pip install -e .`
- [ ] Tests import from `isthisstockgood` package
- [ ] Tests run successfully: `uv run pytest`

## Complete Fresh Setup

If you're starting from scratch or want to reset:

```bash
# 1. Navigate to project root
cd /path/to/your/project

# 2. Remove old virtual environment (if exists)
rm -rf .venv

# 3. Create fresh virtual environment
uv venv

# 4. Activate it
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# 5. Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# 6. Verify installation
uv run python -c "import isthisstockgood; print('Success!')"

# 7. Run tests
uv run pytest -v
```

## VS Code / PyCharm Configuration

### VS Code settings.json

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ],
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

### PyCharm

1. Go to **Settings** → **Project Structure**
2. Mark `isthisstockgood` as **Sources Root**
3. Mark `tests` as **Test Sources Root**
4. Set Python interpreter to `.venv/bin/python`

## Debugging Import Issues

### Check Python path

```bash
uv run python -c "import sys; print('\n'.join(sys.path))"
```

Should include your project root.

### Check if package is importable

```bash
uv run python -c "
import isthisstockgood
print(f'Package location: {isthisstockgood.__file__}')
print(f'Package version: {isthisstockgood.__version__}')
"
```

### Test import in interactive shell

```bash
uv run python
>>> import isthisstockgood
>>> from isthisstockgood.YFinanceData import YFinanceData
>>> YFinanceData('AAPL')
>>> exit()
```

## Summary

The **key solution** is installing your package in editable mode:

```bash
uv pip install -e .
```

This makes `isthisstockgood` importable from anywhere, allowing your tests to run successfully. Make sure you have `__init__.py` files in both `isthisstockgood/` and `tests/` directories.
