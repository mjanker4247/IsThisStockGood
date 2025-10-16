# IsThisStockGood

[![IsThisStockGood](https://github.com/mrhappyasthma/IsThisStockGood/actions/workflows/python-app.yml/badge.svg)](https://github.com/mrhappyasthma/IsThisStockGood/actions)

[IsThisStockGood.com](http://www.isthisstockgood.com)

This website attempts to automate much of the calculations described in Phil Town's
[Rule #1](https://www.amazon.com/gp/product/0307336840?pf_rd_p=c2945051-950f-485c-b4df-15aac5223b10&pf_rd_r=WVNPVWRWTJ9E0QSDGWTH) investing book.
(As well as his second book, [Payback Time](https://www.amazon.com/Payback-Time-Outsmarting-Getting-Investments/dp/1847940641/).)

To use the website, simply enter in a stock ticker symbol and let this site do its magic.

The data for this website is pulled from various sources such as Morningstar, Yahoo
Finance, MSN Money, etc.

If you wanted to mirror many of these calculations in a spreadsheet, you can
check out Phil Town's [PDF](https://www.ruleoneinvesting.com/ExcelFormulas.pdf)
explaining this step-by-step.

NOTE: This site is for personal investing purposes only. Any analysis on this site
should be used at your own discretion. Obviously investing always carries some risk,
but if you follow the principles in Rule #1 investing, then this site should be a
"one stop shop" for all the calculations/resources you may need.

## Stock Screening

If you want to run bulk queries for stock analysis, check out the [Rule 1 Stock Screener](https://github.com/mrhappyasthma/Rule1-StockScreener) repository.

This repository contains a script to iteratively issue a bulk fetch and populate a MySQL database with the results. It also includes some predefined SQL queries for convenience.

## Install dependencies

### uv

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) using your preferred method (for example `pipx install uv` or `curl -LsSf https://astral.sh/install.sh | sh`).
2. From the repository root, run `uv sync` to create and populate the managed virtual environment.
3. (Optional) Activate the environment with `source .venv/bin/activate` or rely on `uv run` to execute commands inside it.

## Running the site locally.

1. Clone the repo.
2. Install python3, if you haven't already.
3. Install the dependencies with `uv sync`.
4. Run the application with:
```
uv run python main.py
```

### Runtime configuration

The application can be configured through environment variables, which is useful
when running behind a proxy such as **nginx** or in a Docker service.

| Variable | Default | Description |
| --- | --- | --- |
| `ISG_HOST` | `0.0.0.0` | Network interface for the Flask development server. |
| `ISG_PORT` | `8080` | Port for the Flask development server. |
| `ISG_DEBUG` | `false` | Enables Flask debug mode when set to a truthy value (`1`, `true`, `yes`, etc.). |
| `ISG_REDIRECT_URL` | `https://isthisstockgood.com` | Target URL for legacy App Engine redirects (set empty to disable). |
| `ISG_REDIRECT_HOST_SUFFIX` | `.appspot.com` | Host suffix that triggers a redirect to `ISG_REDIRECT_URL`. |
| `ISG_ENABLE_REDIRECT` | `true` | Toggle for redirect behaviour; set to `false` to serve responses directly. |

Example Docker invocation:

```
docker run -p 8080:8080 \
  -e ISG_HOST=0.0.0.0 \
  -e ISG_PORT=8080 \
  -e ISG_DEBUG=false \
  -e ISG_ENABLE_REDIRECT=false \
  your-image-name
```

## Testing

The automated test suite can be executed with:

```
uv run pytest
```

To capture line coverage data without relying on third-party plugins, run:

```
uv run tools/run_tests_with_coverage.py
```

The coverage helper leverages Python's built-in tracing facilities and writes raw execution
artifacts to `coverage_report/` while printing a human-readable summary to the console.

## Deploying the site

If you haven't already, install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

If it's your first time deploying, run:

```
gcloud init
```

If you already have an initialized repository, then simply run

```
gcloud app deploy app.yaml
```
