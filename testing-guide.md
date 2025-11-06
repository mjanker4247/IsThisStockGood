# Testing Guide for YFinance Data Fetcher

## Overview

This test suite verifies the correct functionality of the yfinance data fetcher and validates all returned variables.

## Test Coverage

### 1. **YFinanceData Class Tests** (`TestYFinanceData`)

#### Initialization Tests
- ✅ Proper object initialization with correct default values
- ✅ Ticker symbol normalization (uppercase, trimming)

#### Calculation Tests
- ✅ CAGR (Compound Annual Growth Rate) calculation
  - Positive values
  - Negative values
  - Edge cases (zero, None values)
- ✅ Growth rate computation for different time periods (1yr, 3yr, 5yr, max)
- ✅ Average computation for different time periods

#### Data Extraction Tests
- ✅ Company info extraction (name, description, industry, price, volume)
- ✅ EPS extraction from income statements
- ✅ Debt metrics extraction (total debt, debt-to-equity ratio)

### 2. **DataFetcher Module Tests** (`TestDataFetcher`)

#### Success Cases
- ✅ Successful data fetching and processing
- ✅ Correct structure of returned dictionary
- ✅ All required keys present in response
- ✅ Correct data types for all fields

#### Calculation Validation
- ✅ Ten cap price calculation (10 × Free Cash Flow per share)
- ✅ Debt payoff time calculation (Total Debt / Free Cash Flow)

#### Error Handling
- ✅ Invalid ticker symbols (empty, None)
- ✅ API failure handling

### 3. **Integration Tests** (`TestIntegration`)

- ✅ Real API calls with AAPL and MSFT (skipped by default to avoid rate limits)

## Running the Tests

### Basic Usage

```bash
# Run all tests
python test_yfinance_data.py

# Run with verbose output
python -m unittest test_yfinance_data.TestYFinanceData -v

# Run specific test class
python -m unittest test_yfinance_data.TestDataFetcher -v

# Run specific test method
python -m unittest test_yfinance_data.TestYFinanceData.test_cagr_calculation_positive_values -v
```

### Running Integration Tests (Real API Calls)

By default, integration tests are skipped to avoid API rate limits. To enable them:

1. Remove the `@unittest.skip()` decorator from the test methods
2. Run the tests:
   ```bash
   python -m unittest test_yfinance_data.TestIntegration -v
   ```

## Expected Output

```
test_initialization (test_yfinance_data.TestYFinanceData) ... ok
test_ticker_symbol_normalization (test_yfinance_data.TestYFinanceData) ... ok
test_cagr_calculation_positive_values (test_yfinance_data.TestYFinanceData) ... ok
test_cagr_calculation_negative_values (test_yfinance_data.TestYFinanceData) ... ok
test_cagr_calculation_edge_cases (test_yfinance_data.TestYFinanceData) ... ok
test_compute_growth_rates (test_yfinance_data.TestYFinanceData) ... ok
test_compute_averages (test_yfinance_data.TestYFinanceData) ... ok
test_fetch_info_success (test_yfinance_data.TestYFinanceData) ... ok
test_extract_eps (test_yfinance_data.TestYFinanceData) ... ok
test_extract_debt_metrics (test_yfinance_data.TestYFinanceData) ... ok
test_fetch_data_for_ticker_symbol_success (test_yfinance_data.TestDataFetcher) ... ok
test_fetch_data_invalid_ticker (test_yfinance_data.TestDataFetcher) ... ok
test_fetch_data_api_failure (test_yfinance_data.TestDataFetcher) ... ok
test_ten_cap_price_calculation (test_yfinance_data.TestDataFetcher) ... ok
test_debt_payoff_time_calculation (test_yfinance_data.TestDataFetcher) ... ok

======================================================================
TEST SUMMARY
======================================================================
Tests run: 15
Successes: 15
Failures: 0
Errors: 0
Skipped: 2
======================================================================
```

## Validated Return Variables

The test suite validates that `fetchDataForTickerSymbol()` returns a dictionary with these keys:

### Required Keys

| Key | Type | Description | Test Validation |
|-----|------|-------------|-----------------|
| `ticker` | str | Stock ticker symbol | ✅ Type check |
| `name` | str | Company name | ✅ Type check, non-empty |
| `description` | str | Company description | ✅ Type check |
| `roic` | list | Return on Invested Capital averages | ✅ Type check, list |
| `eps` | list | EPS growth rates | ✅ Type check, list |
| `sales` | list | Revenue growth rates | ✅ Type check, list |
| `equity` | list | Equity growth rates | ✅ Type check, list |
| `cash` | list | Free cash flow growth rates | ✅ Type check, list |
| `total_debt` | float | Total debt amount | ✅ Type check, numeric |
| `free_cash_flow` | float | Free cash flow | ✅ Type check, numeric |
| `ten_cap_price` | float | 10 × FCF per share | ✅ Calculation validation |
| `debt_payoff_time` | int | Years to pay off debt | ✅ Calculation validation |
| `debt_equity_ratio` | float | Debt-to-equity ratio | ✅ Type check, numeric |
| `margin_of_safety_price` | float/str | Margin of safety price | ✅ Type check |
| `current_price` | float/str | Current stock price | ✅ Type check |
| `sticker_price` | float/str | Sticker price | ✅ Type check |
| `payback_time` | float/str | Payback time in years | ✅ Type check |
| `average_volume` | float/str | Average trading volume | ✅ Type check |

### Value Types

- **Numeric values**: `float` or `int`
- **List values**: Always `list` (may be empty `[]` if data unavailable)
- **Nullable values**: May be `'null'` string if data unavailable

## Test Data Validation

### CAGR Calculation Example

```python
# Input: Start value = 100, End value = 110, Years = 1
# Expected: 10% growth
# Test validates: result ≈ 10.0 (within 2 decimal places)
```

### Ten Cap Price Calculation Example

```python
# Input: FCF per share = $10
# Expected: 10 × $10 = $100
# Test validates: ten_cap_price == 100.0
```

### Debt Payoff Time Calculation Example

```python
# Input: Total debt = $10M, FCF = $5M/year
# Expected: 10 / 5 = 2 years
# Test validates: debt_payoff_time == 2
```

## Mocking Strategy

The tests use `unittest.mock` to avoid real API calls:

1. **Mock yfinance.Ticker**: Returns controlled test data
2. **Mock YFinanceData**: Returns predictable values for calculation tests
3. **Isolated testing**: Each component tested independently

## Adding New Tests

To add a new test:

```python
def test_your_new_feature(self):
    """Description of what you're testing"""
    # Arrange: Set up test data
    test_input = "TEST"
    
    # Act: Execute the function
    result = your_function(test_input)
    
    # Assert: Verify the results
    self.assertEqual(result, expected_value)
```

## Continuous Integration

These tests are suitable for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    python test_yfinance_data.py
```

## Dependencies

Required for testing:
```
yfinance>=0.2.40
pandas>=1.5.0
unittest (built-in)
unittest.mock (built-in)
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:
```bash
# Ensure you're in the correct directory
cd /path/to/isthisstockgood

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/isthisstockgood"
```

### API Rate Limiting

If integration tests fail due to rate limits:
- Keep the `@unittest.skip()` decorator
- Use mocked tests for CI/CD
- Run integration tests manually and infrequently

## Coverage Report

To generate a coverage report:

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m unittest test_yfinance_data

# Generate report
coverage report -m

# Generate HTML report
coverage html
```

Expected coverage: **>90%** for YFinanceData and DataFetcher modules.
