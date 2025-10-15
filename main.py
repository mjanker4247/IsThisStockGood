"""Application entry point for the IsThisStockGood service."""

import os

from isthisstockgood.DataFetcher import fetchDataForTickerSymbol
from isthisstockgood.server import create_app


def _as_bool(value, default=False):
    """Convert a value from the environment into a boolean."""
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


# Expose `app` object at the module level, as expected by App Engine
app = create_app(fetchDataForTickerSymbol)

if __name__ == '__main__':
    host = os.environ.get('ISG_HOST', '0.0.0.0')
    port = int(os.environ.get('ISG_PORT', '8080'))
    debug = _as_bool(os.environ.get('ISG_DEBUG'), default=False)

    app.run(host=host, port=port, debug=debug)
