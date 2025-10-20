from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Callable, Mapping, Optional

from flask import (
    Flask,
    Response,
    json,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.urls import url_parse

from .config import AppConfig, configure_logger
from .i18n import SUPPORTED_LANGUAGES, get_language, get_translations

StockDataFetcher = Callable[[str], Optional[Mapping[str, Any]]]


LANGUAGE_COOKIE_NAME = "isg_lang"
DEFAULT_LANGUAGE_CODE = "en"
LANGUAGE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


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

    def ensure_supported_language(language_code: str | None) -> str:
        if language_code and language_code in SUPPORTED_LANGUAGES:
            return language_code
        return DEFAULT_LANGUAGE_CODE

    def get_requested_language() -> str:
        query_language = ensure_supported_language(request.args.get("lang"))
        if query_language != DEFAULT_LANGUAGE_CODE or "lang" in request.args:
            return query_language

        cookie_language = ensure_supported_language(request.cookies.get(LANGUAGE_COOKIE_NAME))
        return cookie_language

    def attach_language_cookie(response: Response, language_code: str) -> Response:
        response.set_cookie(
            LANGUAGE_COOKIE_NAME,
            language_code,
            max_age=LANGUAGE_COOKIE_MAX_AGE,
            samesite="Lax",
        )
        return response

    def build_base_template_context(language_code: str) -> dict[str, Any]:
        translations = get_translations(language_code)
        language = get_language(language_code)
        return {
            "page_title": translations["global"]["page_title"],
            "current_year": date.today().year,
            "t": translations,
            "translations": translations,
            "language_code": language.code,
            "language": language,
            "supported_languages": SUPPORTED_LANGUAGES,
        }

    def build_redirect_target(next_url: str | None) -> str:
        fallback_url = url_for("homepage")
        if not next_url:
            return fallback_url

        parsed_url = url_parse(next_url)
        if parsed_url.netloc and parsed_url.netloc != request.host:
            return fallback_url

        path = parsed_url.path or "/"
        if parsed_url.query:
            return f"{path}?{parsed_url.query}"
        return path

    @app.route("/api/ticker/<string:ticker>")
    def api_ticker(ticker: str) -> Response:
        language_code = get_requested_language()
        translations = get_translations(language_code)
        template_values = fetch_data_for_ticker(ticker or app.config["ISG_DEFAULT_TICKER"])

        if not template_values:
            data = render_template(
                "json/error.json",
                error=translations["api"]["invalid_ticker"],
            )
        else:
            data = render_template("json/stock_data.json", **template_values)

        response = app.response_class(response=data, status=200, mimetype="application/json")
        return attach_language_cookie(response, language_code)

    @app.route("/api")
    def api() -> Response:
        data: Mapping[str, Any] = {}
        return app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype="application/json",
        )

    @app.route("/set-language", methods=["POST"])
    def set_language() -> Response:
        language_code = ensure_supported_language(request.form.get("language"))
        next_url = build_redirect_target(request.form.get("next"))
        response = redirect(next_url)
        return attach_language_cookie(response, language_code)

    @app.route("/")
    def homepage() -> Response | str:
        redirect_response = maybe_redirect()
        if redirect_response:
            return redirect_response

        language_code = get_requested_language()
        template_values = build_base_template_context(language_code)
        response = make_response(render_template("home.html", **template_values))
        return attach_language_cookie(response, language_code)

    @app.route("/search", methods=["POST"])
    def search() -> Response | str:
        redirect_response = maybe_redirect()
        if redirect_response:
            return redirect_response

        ticker = request.values.get("ticker", "")
        language_code = get_requested_language()
        translations = get_translations(language_code)
        template_values = fetch_data_for_ticker(ticker)
        if not template_values:
            data = render_template(
                "json/error.json",
                error=translations["api"]["invalid_ticker"],
            )
            response = app.response_class(response=data, status=200, mimetype="application/json")
            return attach_language_cookie(response, language_code)

        data = render_template("json/stock_data.json", **template_values)
        response = app.response_class(response=data, status=200, mimetype="application/json")
        return attach_language_cookie(response, language_code)

    return app


__all__ = ["create_app", "StockDataFetcher"]
