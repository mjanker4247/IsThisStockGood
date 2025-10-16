# IsThisStockGood API Documentation

The IsThisStockGood service exposes a lightweight JSON API that aggregates stock metrics from multiple upstream providers and computes Rule #1 investing indicators. This document describes the available endpoints, expected request and response formats, and tips for local development and testing.

## Base URL

When running locally the API is served from `http://localhost:8080`. In production the base URL depends on your deployment target but the routes remain the same.

## Authentication

The API is currently public and does not require authentication. If you deploy the application to a hosted environment you should place it behind an authenticated proxy or gateway before sharing it broadly.

## Content Type

Every endpoint returns `application/json` responses encoded as UTF-8.

## Endpoints

### `GET /api`

Returns an empty JSON object. This endpoint can be used as a lightweight health check.

```
HTTP/1.1 200 OK
Content-Type: application/json

{}
```

### `GET /api/ticker/<ticker>`

Resolve `<ticker>` to a stock symbol (including ISIN support) and return the computed fundamentals for that security. The response body mirrors the `stock_data.json` template used by the frontend and contains the metrics required by the Rule #1 investing methodology.

Successful response example:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "ticker": "MSFT",
  "identifier": "msft",
  "identifier_type": "ticker",
  "identifier_resolution_succeeded": true,
  "name": "Microsoft Corporation",
  "description": "Microsoft Corporation provides software, services, devices, and solutions.",
  "roic": [36.7, 35.1, 33.46],
  "eps": [7.69, 8.37],
  "sales": [4.56, 4.67],
  "equity": [4.17, 6.62],
  "cash": [6.12, 7.38],
  "total_debt": 65000000000.0,
  "free_cash_flow": 39000000000,
  "debt_payoff_time": 2,
  "debt_equity_ratio": 0.435,
  "margin_of_safety_price": 21.27928049415012,
  "current_price": 330.12,
  "sticker_price": 42.55856098830024,
  "payback_time": 22,
  "ten_cap_price": 52.0,
  "average_volume": 25000000
}
```

If the identifier cannot be resolved or upstream providers return invalid payloads, the service still responds with HTTP 200 but renders an error template containing an explanatory message.

```
HTTP/1.1 200 OK
Content-Type: application/json

{"error": "Invalid ticker symbol"}
```

### `POST /search`

Submit a form-encoded body containing a `ticker` parameter. The endpoint resolves the identifier using the same pipeline as `GET /api/ticker/<ticker>` and renders the same JSON template in the response.

### `GET /`

Render the HTML homepage. When redirect rules are enabled in the configuration the request may receive a `302` redirect to the configured marketing URL. Otherwise the page renders static marketing content.

## Error Handling

All endpoints return HTTP 200 responses even when an identifier cannot be resolved. The `identifier_resolution_succeeded` flag and optional `error` payload can be used to detect and display failures to end users.

## Rate Limiting & Performance

The application randomizes outbound user agents and performs upstream calls concurrently. For testing and development you can patch the data fetchers with the fixtures under `tests/conftest.py` to avoid hitting live services. Automated tests include performance checks that assert the entire aggregation pipeline completes within the configured budget when using the canned payloads.

## Testing & Coverage

Run the full automated test suite with code coverage enabled:

```
tools/run_tests_with_coverage.py
```

The helper script wraps `pytest` with Python's standard library tracing facilities and writes a human readable summary to
`coverage_report/coverage.txt` alongside raw line execution counts for each module.
