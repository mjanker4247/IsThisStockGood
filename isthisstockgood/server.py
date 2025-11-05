"""Flask application factory and HTTP endpoints."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, MutableMapping

from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from isthisstockgood.config import AppConfig, configure_logger

JsonFetcher = Callable[[str], MutableMapping[str, Any] | None]


@dataclass(frozen=True)
class _RouteContext:
    """Bundle dependencies used across view functions."""

    fetcher: JsonFetcher
    config: AppConfig
    logger: logging.Logger


def _should_redirect_host(host: str, config: AppConfig) -> bool:
    """Determine whether ``host`` should be redirected to the canonical domain."""

    if not config.enable_redirect:
        return False
    return host.endswith(config.redirect_host_suffix)


def _build_api_blueprint(ctx: _RouteContext) -> Blueprint:
    """Create the API blueprint exposing JSON endpoints."""

    blueprint = Blueprint("api", __name__, url_prefix="/api")

    @blueprint.get("/")
    def heartbeat() -> Response:
        return jsonify({})

    @blueprint.get("/ticker/<string:identifier>")
    def ticker(identifier: str) -> Response:
        data = ctx.fetcher(identifier)
        if not data:
            ctx.logger.warning("No data returned for ticker %s", identifier)
            return jsonify({"error": "Invalid ticker symbol"}), 404
        return jsonify(data)

    return blueprint


def _build_pages_blueprint(ctx: _RouteContext) -> Blueprint:
    """Create the blueprint serving HTML templates."""

    blueprint = Blueprint("pages", __name__)

    @blueprint.get("/")
    def homepage() -> Response:
        host = request.host or ""
        if _should_redirect_host(host, ctx.config):
            ctx.logger.info("Redirecting request for %s to %s", host, ctx.config.redirect_url)
            return redirect(ctx.config.redirect_url, code=302)

        template_values = {
            "page_title": "Is This Stock Good?",
            "current_year": date.today().year,
        }
        return render_template("home.html", **template_values)

    @blueprint.post("/search")
    def search() -> Response:
        host = request.host or ""
        if _should_redirect_host(host, ctx.config):
            ctx.logger.info("Redirecting search request for %s to %s", host, ctx.config.redirect_url)
            return redirect(ctx.config.redirect_url, code=302)

        ticker = request.values.get("ticker", "").strip().upper()
        if not ticker:
            return render_template("json/error.json", error="Ticker symbol is required"), 400

        data = ctx.fetcher(ticker)
        if not data:
            return render_template("json/error.json", error="Invalid ticker symbol"), 404

        return render_template("json/stock_data.json", **data)

    return blueprint


def create_app(
    fetcher: JsonFetcher,
    *,
    config: AppConfig | None = None,
    logger: logging.Logger | None = None,
) -> Flask:
    """Create a fully configured Flask application instance."""

    resolved_config = config or AppConfig()
    resolved_logger = logger or configure_logger(resolved_config.logger_name, resolved_config.log_level)

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    ctx = _RouteContext(fetcher=fetcher, config=resolved_config, logger=resolved_logger)

    app.register_blueprint(_build_api_blueprint(ctx))
    app.register_blueprint(_build_pages_blueprint(ctx))

    @app.before_request
    def _inject_dependencies() -> None:  # pragma: no cover - defensive guard
        current_app.config.setdefault("APP_CONFIG", resolved_config)
        current_app.config.setdefault("APP_LOGGER", resolved_logger)

    return app
