# Repository Analysis Plan

## Overview
This document captures the current issues identified in the `IsThisStockGood` repository and outlines a plan for addressing them. The focus is on restoring functionality after the migration to the new yfinance-based data pipeline and removing obsolete infrastructure.

## Issues Identified

1. **Hard-coded API ticker route**  
   *Location:* `app/server.py` route definition.  
   The `/api/ticker/nvda` endpoint is hard-coded to always fetch the NVDA ticker instead of accepting a dynamic ticker parameter. This breaks the REST contract and prevents consumers from querying other symbols through the API. 【F:app/server.py†L23-L34】

2. **Out-of-date tests referencing removed modules**  
   *Location:* `tests/test_DataSources.py`, `tests/test_financial_fetcher.py`, `tests/test_MSNMoney.py`.  
   These tests still import the legacy `DataFetcher` class and the `MSNMoney` scraper that no longer exist. They will fail (or even raise import errors) under the current codebase, masking regressions and preventing CI from providing meaningful feedback. 【F:tests/test_DataSources.py†L1-L51】【F:tests/test_financial_fetcher.py†L1-L31】【F:tests/test_MSNMoney.py†L1-L42】

3. **Missing analyst growth rate retrieval in yfinance pipeline**  
   *Location:* `app/DataFetcher.py` in `fetchDataForTickerSymbol`.  
   The logic expects `YFinanceData.five_year_growth_rate` to be set, but `YFinanceData.fetch_all_data()` never calls `fetch_five_year_growth_rate()`. As a result, growth-dependent calculations (margin of safety, payback time) often return `None`, degrading key valuation outputs. 【F:app/DataFetcher.py†L34-L75】【F:app/YFinanceData.py†L45-L118】【F:app/YFinanceData.py†L188-L232】

4. **JSON templates emit string literals for missing numeric values**  
   *Location:* `app/templates/json/stock_data.json`.  
   The template injects placeholder strings such as `'null'` for missing values, which renders as the string "null" inside JSON rather than the JSON literal `null`. This violates the API contract and complicates client parsing. 【F:app/DataFetcher.py†L81-L108】【F:app/templates/json/stock_data.json†L1-L19】

## Remediation Plan

### 1. Parameterize the API ticker route
- Update `app/server.py` to expose `/api/ticker/<ticker>` while preserving backwards compatibility (e.g., redirect or alias for `/api/ticker/nvda`).
- Adjust the handler to validate the incoming ticker, leverage `fetchDataForTickerSymbol`, and return appropriate error responses.
- Update or add tests in `tests/test_api.py` to cover dynamic ticker queries.

### 2. Modernize the test suite
- Remove or rewrite tests that reference legacy modules so that they target the current yfinance-driven implementation. Focus on high-level API contract tests and unit tests for `YFinanceData`/`DataFetcher` helper functions.
- Introduce fixtures or mocks to avoid live network calls to yfinance and external websites, ensuring deterministic results.
- Ensure CI executes without external dependencies by providing sample responses or cached fixtures in `testdata/`.

### 3. Restore analyst growth rate support
- Invoke `YFinanceData.fetch_five_year_growth_rate()` from `fetch_all_data()` (guarded to avoid unnecessary scraping when `five_year_growth_rate` already populated via yfinance).
- Refine `_calculateMarginOfSafetyPrice` and `_calculatePaybackTime` to handle missing growth data gracefully and document fallbacks.
- Expand unit coverage for growth-dependent calculations to verify realistic outputs under different data availability scenarios.

### 4. Emit canonical JSON nulls for absent data
- Replace the manual string placeholders in `DataFetcher` with Python `None` values.
- Update the Jinja templates to use the `|tojson` filter, guaranteeing correct JSON encoding for lists, numbers, and nulls.
- Add regression tests asserting that the serialized JSON uses proper nulls and numeric precision.

## Testing Strategy
For code changes implementing this plan, run the following:
- Unit tests: `pytest tests/` (with network interactions mocked).
- API contract tests against the Flask test client to validate status codes and payloads.
- Any newly added static analysis or linting checks (e.g., `ruff`, `flake8`) to enforce style consistency after refactors.
- Where applicable, include regression tests for calculations impacted by the growth-rate updates.
