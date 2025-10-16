"""Application configuration helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Mapping, Sequence


def _as_bool(value: object, default: bool = False) -> bool:
    """Convert ``value`` into a boolean."""

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _parse_user_agents(value: str | None, default: Sequence[str]) -> Sequence[str]:
    """Parse the configured list of HTTP user agents."""

    if not value:
        return tuple(default)

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ValueError("ISG_USER_AGENTS must be valid JSON") from exc

    if not isinstance(parsed_value, list) or not all(isinstance(item, str) for item in parsed_value):
        raise ValueError("ISG_USER_AGENTS must be a JSON list of strings")

    return tuple(parsed_value)


def _parse_log_level(value: str | None, default: int) -> int:
    """Parse the configured log level."""

    if not value:
        return default

    resolved_level = logging.getLevelName(value.upper())
    if isinstance(resolved_level, int):
        return resolved_level

    raise ValueError(f"Unknown log level: {value}")


def configure_logger(name: str, level: int) -> logging.Logger:
    """Create or configure an application wide logger."""

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

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> "AppConfig":
        """Create configuration from ``environ`` values."""

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
        user_agents = _parse_user_agents(environ.get("ISG_USER_AGENTS"), cls().user_agents)

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
        )


__all__ = ["AppConfig", "configure_logger", "_as_bool"]
