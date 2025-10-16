"""Application configuration helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Mapping, Sequence


def _as_bool(value: object, default: bool = False) -> bool:
    """Convert ``value`` into a boolean.

    Args:
        value: The potential boolean value supplied via configuration.
        default: The fallback value when ``value`` is ``None``.

    Returns:
        ``True`` or ``False`` depending on the interpreted string or native bool.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _parse_string_sequence(
    value: str | None,
    default: Sequence[str],
    *,
    setting_name: str,
) -> Sequence[str]:
    """Parse a JSON encoded list of strings from configuration."""

    if not value:
        return tuple(default)

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"{setting_name} must be valid JSON") from exc

    if not isinstance(parsed_value, list) or not all(isinstance(item, str) for item in parsed_value):
        raise ValueError(f"{setting_name} must be a JSON list of strings")

    return tuple(parsed_value)


def _parse_user_agents(value: str | None, default: Sequence[str]) -> Sequence[str]:
    """Parse the configured list of HTTP user agents."""

    return _parse_string_sequence(value, default, setting_name="ISG_USER_AGENTS")


def _parse_log_level(value: str | None, default: int) -> int:
    """Parse the configured log level.

    Args:
        value: Raw log level name (e.g. ``"INFO"``) from configuration.
        default: Fallback numeric level when ``value`` is empty.

    Returns:
        The numeric logging level constant understood by :mod:`logging`.
    """

    if not value:
        return default

    resolved_level = logging.getLevelName(value.upper())
    if isinstance(resolved_level, int):
        return resolved_level

    raise ValueError(f"Unknown log level: {value}")


def configure_logger(name: str, level: int) -> logging.Logger:
    """Create or configure an application wide logger.

    Args:
        name: The logger name to create or reuse.
        level: The minimum log level that should be emitted.

    Returns:
        A configured :class:`logging.Logger` instance with a stream handler attached.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s : %(message)s"))
        logger.addHandler(handler)

    logger.propagate = False
    return logger


@dataclass(frozen=True)
class AppConfig:
    """Strongly typed application configuration values."""

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    redirect_url: str = "https://isthisstockgood.com"
    redirect_host_suffix: str = ".appspot.com"
    enable_redirect: bool = True
    default_ticker: str = "NVDA"
    logger_name: str = "IsThisStockGood"
    log_level: int = logging.WARNING
    user_agents: Sequence[str] = field(
        default_factory=lambda: (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        )
    )
    msn_money_api_key: str | None = None
    rate_limit_default: str = "60 per minute"
    rate_limit_api_ticker: str = "120 per minute"
    rate_limit_search: str = "30 per minute"
    rate_limit_storage_uri: str = "memory://"
    cors_allow_origins: Sequence[str] = field(default_factory=tuple)
    cors_allow_methods: Sequence[str] = field(default_factory=lambda: ("GET", "POST", "OPTIONS"))
    cors_allow_headers: Sequence[str] = field(default_factory=lambda: ("Content-Type", "Authorization"))
    cors_allow_credentials: bool = False
    cors_max_age: int = 600

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> "AppConfig":
        """Create configuration from ``environ`` values.

        Args:
            environ: Environment mapping, typically :data:`os.environ`.

        Returns:
            A fully-populated :class:`AppConfig` instance with parsed overrides.
        """

        defaults = cls()

        host = environ.get("ISG_HOST", cls.host)
        port_value = environ.get("ISG_PORT")
        port = int(port_value) if port_value else cls.port

        debug = _as_bool(environ.get("ISG_DEBUG"), default=cls.debug)
        redirect_url = environ.get("ISG_REDIRECT_URL", cls.redirect_url)
        redirect_host_suffix = environ.get("ISG_REDIRECT_HOST_SUFFIX", cls.redirect_host_suffix)
        enable_redirect = _as_bool(environ.get("ISG_ENABLE_REDIRECT"), default=cls.enable_redirect)
        default_ticker = environ.get("ISG_DEFAULT_TICKER", cls.default_ticker)
        logger_name = environ.get("ISG_LOGGER_NAME", cls.logger_name)
        log_level = _parse_log_level(environ.get("ISG_LOG_LEVEL"), cls.log_level)
        user_agents = _parse_user_agents(environ.get("ISG_USER_AGENTS"), defaults.user_agents)
        msn_money_api_key = environ.get("ISG_MSN_MONEY_API_KEY", cls.msn_money_api_key)
        rate_limit_default = environ.get("ISG_RATE_LIMIT_DEFAULT", cls.rate_limit_default)
        rate_limit_api_ticker = environ.get("ISG_RATE_LIMIT_API_TICKER", cls.rate_limit_api_ticker)
        rate_limit_search = environ.get("ISG_RATE_LIMIT_SEARCH", cls.rate_limit_search)
        rate_limit_storage_uri = environ.get("ISG_RATE_LIMIT_STORAGE_URI", cls.rate_limit_storage_uri)
        cors_allow_origins = _parse_string_sequence(
            environ.get("ISG_CORS_ALLOW_ORIGINS"),
            defaults.cors_allow_origins,
            setting_name="ISG_CORS_ALLOW_ORIGINS",
        )
        cors_allow_methods = _parse_string_sequence(
            environ.get("ISG_CORS_ALLOW_METHODS"),
            defaults.cors_allow_methods,
            setting_name="ISG_CORS_ALLOW_METHODS",
        )
        cors_allow_headers = _parse_string_sequence(
            environ.get("ISG_CORS_ALLOW_HEADERS"),
            defaults.cors_allow_headers,
            setting_name="ISG_CORS_ALLOW_HEADERS",
        )
        cors_allow_credentials = _as_bool(
            environ.get("ISG_CORS_ALLOW_CREDENTIALS"),
            default=cls.cors_allow_credentials,
        )
        cors_max_age_value = environ.get("ISG_CORS_MAX_AGE")
        cors_max_age = int(cors_max_age_value) if cors_max_age_value else cls.cors_max_age

        return cls(
            host=host,
            port=port,
            debug=debug,
            redirect_url=redirect_url,
            redirect_host_suffix=redirect_host_suffix,
            enable_redirect=enable_redirect,
            default_ticker=default_ticker,
            logger_name=logger_name,
            log_level=log_level,
            user_agents=user_agents,
            msn_money_api_key=msn_money_api_key,
            rate_limit_default=rate_limit_default,
            rate_limit_api_ticker=rate_limit_api_ticker,
            rate_limit_search=rate_limit_search,
            rate_limit_storage_uri=rate_limit_storage_uri,
            cors_allow_origins=cors_allow_origins,
            cors_allow_methods=cors_allow_methods,
            cors_allow_headers=cors_allow_headers,
            cors_allow_credentials=cors_allow_credentials,
            cors_max_age=cors_max_age,
        )


__all__ = ["AppConfig", "configure_logger", "_as_bool"]
