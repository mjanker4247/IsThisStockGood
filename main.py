"""Application entrypoint exposing the Flask WSGI app."""

from __future__ import annotations

import os
from functools import partial

from flask import Flask

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol
from isthisstockgood.config import AppConfig, configure_logger
from isthisstockgood.server import create_app


def _build_app() -> Flask:
    config = AppConfig.from_environ(os.environ)
    logger = configure_logger(config.logger_name, config.log_level)
    fetcher = partial(
        fetch_data_for_ticker_symbol,
        user_agents=config.user_agents,
        alpha_vantage_api_key=config.alpha_vantage_api_key,
    )
    app = create_app(fetcher, config=config, logger=logger)
    app.config["APP_CONFIG"] = config
    app.config["APP_LOGGER"] = logger
    return app


# Expose `app` object at the module level, as expected by App Engine and gunicorn.
app = _build_app()


if __name__ == "__main__":
    app_config: AppConfig = app.config.get("APP_CONFIG", AppConfig())
    app.run(host=app_config.host, port=app_config.port, debug=app_config.debug)
