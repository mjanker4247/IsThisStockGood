"""Application entry point for the IsThisStockGood service."""

from __future__ import annotations

import os
from functools import partial

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol
from isthisstockgood.config import AppConfig, configure_logger
from isthisstockgood.server import create_app


APP_CONFIG = AppConfig.from_environ(os.environ)
LOGGER = configure_logger(APP_CONFIG.logger_name, APP_CONFIG.log_level)

fetcher = partial(fetch_data_for_ticker_symbol, user_agents=APP_CONFIG.user_agents)

# Expose `app` object at the module level, as expected by App Engine
app = create_app(fetcher, config=APP_CONFIG, logger=LOGGER)

if __name__ == '__main__':
    app.run(host=APP_CONFIG.host, port=APP_CONFIG.port, debug=APP_CONFIG.debug)
