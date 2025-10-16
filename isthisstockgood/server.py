from __future__ import annotations

import logging
import os
import re
from datetime import date
from http import HTTPStatus
from typing import Any, Callable, Mapping, Optional

from flask import Flask, Response, json, redirect, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

from .config import AppConfig, configure_logger

StockDataFetcher = Callable[[str], Optional[Mapping[str, Any]]]
INVALID_TICKER_MESSAGE = "Invalid ticker symbol"
TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,9}$")

CSP_DIRECTIVES = (
    "default-src 'self'",
    "script-src 'self' https://ajax.googleapis.com https://cdnjs.cloudflare.com "
    "https://cdn.rawgit.com https://maxcdn.bootstrapcdn.com https://cdn.jsdelivr.net",
    "style-src 'self' https://fonts.googleapis.com https://unpkg.com https://cdn.rawgit.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data:",
    "connect-src 'self'",
    "form-action 'self'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
)


def create_app(
    fetch_data_for_ticker: StockDataFetcher,
    config: AppConfig | None = None,
    logger: logging.Logger | None = None,
) -> Flask:
    """Create and configure the Flask application.

    Args:
        fetch_data_for_ticker: Callable used to retrieve stock data dictionaries.
        config: Optional application configuration to override environment defaults.
        logger: Optional logger instance shared across the application.

    Returns:
        A fully-configured :class:`flask.Flask` instance ready to serve requests.
    """

    resolved_config = config or AppConfig.from_environ(os.environ)
    resolved_logger = logger or configure_logger(resolved_config.logger_name, resolved_config.log_level)

    if resolved_config.msn_money_api_key and not os.getenv("ISG_MSN_MONEY_API_KEY"):
        os.environ["ISG_MSN_MONEY_API_KEY"] = resolved_config.msn_money_api_key
    elif not resolved_config.msn_money_api_key:
        resolved_logger.warning("MSN Money API key is not configured; data fetching may fail.")

    app = Flask(__name__)
    app.config.from_mapping(
        ISG_REDIRECT_URL=resolved_config.redirect_url,
        ISG_REDIRECT_HOST_SUFFIX=resolved_config.redirect_host_suffix,
        ISG_ENABLE_REDIRECT=resolved_config.enable_redirect,
        ISG_DEFAULT_TICKER=resolved_config.default_ticker,
        ISG_RATE_LIMIT_DEFAULT=resolved_config.rate_limit_default,
        ISG_RATE_LIMIT_API_TICKER=resolved_config.rate_limit_api_ticker,
        ISG_RATE_LIMIT_SEARCH=resolved_config.rate_limit_search,
        ISG_RATE_LIMIT_STORAGE_URI=resolved_config.rate_limit_storage_uri,
        ISG_CORS_ALLOW_ORIGINS=tuple(resolved_config.cors_allow_origins),
        ISG_CORS_ALLOW_METHODS=tuple(resolved_config.cors_allow_methods),
        ISG_CORS_ALLOW_HEADERS=tuple(resolved_config.cors_allow_headers),
        ISG_CORS_ALLOW_CREDENTIALS=resolved_config.cors_allow_credentials,
        ISG_CORS_MAX_AGE=resolved_config.cors_max_age,
    )

    app.logger.handlers = resolved_logger.handlers
    app.logger.setLevel(resolved_logger.level)
    app.logger.propagate = False

    limiter = Limiter(
        get_remote_address,
        app=app,
        storage_uri=resolved_config.rate_limit_storage_uri,
        default_limits=[resolved_config.rate_limit_default]
        if resolved_config.rate_limit_default
        else [],
    )

    def limit_decorator(limit_value: str | None) -> Callable[[Callable[..., Response]], Callable[..., Response]]:
        if limit_value and limit_value.strip():
            return limiter.limit(limit_value)
        return lambda function: function

    def maybe_redirect() -> Optional[Response]:
        redirect_url: str = app.config.get("ISG_REDIRECT_URL")
        redirect_suffix: str = app.config.get("ISG_REDIRECT_HOST_SUFFIX")
        redirect_enabled: bool = app.config.get("ISG_ENABLE_REDIRECT", True)

        if redirect_enabled and redirect_url and redirect_suffix and request.host.endswith(redirect_suffix):
            return redirect(redirect_url, code=302)

        return None

    def _invalid_ticker_response(status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> Response:
        data = render_template("json/error.json", error=INVALID_TICKER_MESSAGE)
        return app.response_class(response=data, status=int(status), mimetype="application/json")

    def _validate_ticker(raw_ticker: str | None, *, allow_default: bool = False) -> tuple[str | None, Optional[Response]]:
        if raw_ticker is None:
            if allow_default:
                return app.config["ISG_DEFAULT_TICKER"], None
            return None, _invalid_ticker_response()

        sanitized = raw_ticker.strip().upper()
        if not sanitized:
            if allow_default:
                return app.config["ISG_DEFAULT_TICKER"], None
            return None, _invalid_ticker_response()

        if not TICKER_PATTERN.fullmatch(sanitized):
            return None, _invalid_ticker_response()

        return sanitized, None

    def _append_vary_header(response: Response, value: str) -> None:
        existing = response.headers.get("Vary")
        if existing:
            vary_values = {item.strip() for item in existing.split(",") if item.strip()}
            vary_values.add(value)
            response.headers["Vary"] = ", ".join(sorted(vary_values))
        else:
            response.headers["Vary"] = value

    allowed_origins = tuple(resolved_config.cors_allow_origins)
    allow_all_origins = "*" in allowed_origins

    def _apply_cors_headers(response: Response) -> Response:
        origin = request.headers.get("Origin")
        should_apply = False
        if allow_all_origins and origin:
            response.headers["Access-Control-Allow-Origin"] = origin if resolved_config.cors_allow_credentials else "*"
            should_apply = True
            if resolved_config.cors_allow_credentials:
                _append_vary_header(response, "Origin")
        elif allowed_origins and origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            should_apply = True
            _append_vary_header(response, "Origin")

        if should_apply:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(resolved_config.cors_allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(resolved_config.cors_allow_headers)
            response.headers["Access-Control-Max-Age"] = str(resolved_config.cors_max_age)
            if resolved_config.cors_allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

    def _apply_security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "; ".join(CSP_DIRECTIVES))
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        if request.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
            )
        return response

    @app.before_request
    def log_request_start() -> None:  # pragma: no cover - logging side effect
        client_address = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        app.logger.info("Incoming request %s %s from %s", request.method, request.path, client_address)

    @app.after_request
    def finalize_response(response: Response) -> Response:  # pragma: no cover - logging side effect
        response = _apply_cors_headers(response)
        response = _apply_security_headers(response)
        client_address = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        app.logger.info(
            "Completed request %s %s with status %s for %s",
            request.method,
            request.path,
            response.status_code,
            client_address,
        )
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Response:
        app.logger.warning("HTTP error %s while processing %s %s", error.code, request.method, request.path)
        payload = json.dumps({"error": error.name})
        return app.response_class(response=payload, status=error.code, mimetype="application/json")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Response:  # pragma: no cover - defensive guard
        app.logger.exception("Unhandled exception while processing request")
        payload = json.dumps({"error": "An unexpected error occurred."})
        return app.response_class(
            response=payload,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/json",
        )

    @app.route("/api/ticker/<string:ticker>")
    @limit_decorator(resolved_config.rate_limit_api_ticker)
    def api_ticker(ticker: str) -> Response:
        normalized_ticker, error_response = _validate_ticker(ticker, allow_default=True)
        if error_response:
            return error_response

        template_values = fetch_data_for_ticker(normalized_ticker or app.config["ISG_DEFAULT_TICKER"])

        if not template_values:
            return _invalid_ticker_response(status=HTTPStatus.NOT_FOUND)

        data = render_template("json/stock_data.json", **template_values)
        return app.response_class(response=data, status=HTTPStatus.OK, mimetype="application/json")

    @app.route("/api")
    @limit_decorator(resolved_config.rate_limit_default)
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
    @limit_decorator(resolved_config.rate_limit_search)
    def search() -> Response | str:
        redirect_response = maybe_redirect()
        if redirect_response:
            return redirect_response

        ticker = request.values.get("ticker")
        normalized_ticker, error_response = _validate_ticker(ticker)
        if error_response:
            return error_response

        template_values = fetch_data_for_ticker(normalized_ticker)
        if not template_values:
            return _invalid_ticker_response(status=HTTPStatus.NOT_FOUND)

        return render_template("json/stock_data.json", **template_values)

    return app


__all__ = ["create_app", "StockDataFetcher"]
