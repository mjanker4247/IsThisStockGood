from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Callable, Mapping, Optional

from flask import Flask, Response, json, redirect, render_template, request

from .config import AppConfig, configure_logger

StockDataFetcher = Callable[[str], Optional[Mapping[str, Any]]]


def create_app(
    fetch_data_for_ticker: StockDataFetcher,
    config: AppConfig | None = None,
    logger: logging.Logger | None = None,
) -> Flask:
    """Create and configure the Flask application."""

    resolved_config = config or AppConfig.from_environ(os.environ)
    resolved_logger = logger or configure_logger(resolved_config.logger_name, resolved_config.log_level)

    app = Flask(__name__)
    app.config.from_mapping(
        ISG_REDIRECT_URL=resolved_config.redirect_url,
        ISG_REDIRECT_HOST_SUFFIX=resolved_config.redirect_host_suffix,
        ISG_ENABLE_REDIRECT=resolved_config.enable_redirect,
        ISG_DEFAULT_TICKER=resolved_config.default_ticker,
    )

    app.logger.handlers = resolved_logger.handlers
    app.logger.setLevel(resolved_logger.level)
    app.logger.propagate = False

    def maybe_redirect() -> Optional[Response]:
        redirect_url: str = app.config.get("ISG_REDIRECT_URL")
        redirect_suffix: str = app.config.get("ISG_REDIRECT_HOST_SUFFIX")
        redirect_enabled: bool = app.config.get("ISG_ENABLE_REDIRECT", True)

        if redirect_enabled and redirect_url and redirect_suffix and request.host.endswith(redirect_suffix):
            return redirect(redirect_url, code=302)

        return None

    @app.route("/api/ticker/<string:ticker>")
    def api_ticker(ticker: str) -> Response:
        template_values = fetch_data_for_ticker(ticker or app.config["ISG_DEFAULT_TICKER"])

        if not template_values:
            data = render_template("json/error.json", error="Invalid ticker symbol")
        else:
            data = render_template("json/stock_data.json", **template_values)

        return app.response_class(response=data, status=200, mimetype="application/json")

    @app.route("/api")
    def api() -> Response:
        data: Mapping[str, Any] = {}
        return app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype="application/json",
        )

    @app.route("/")
    def homepage() -> Response | str:
        redirect_response = maybe_redirect()
        if redirect_response:
            return redirect_response

        template_values = {
            "page_title": "Is This Stock Good?",
            "current_year": date.today().year,
        }
        return render_template("home.html", **template_values)

    @app.route("/search", methods=["POST"])
    def search() -> Response | str:
        redirect_response = maybe_redirect()
        if redirect_response:
            return redirect_response

        ticker = request.values.get("ticker", "")
        template_values = fetch_data_for_ticker(ticker)
        if not template_values:
            return render_template("json/error.json", error="Invalid ticker symbol")

        return render_template("json/stock_data.json", **template_values)

    return app


__all__ = ["create_app", "StockDataFetcher"]
