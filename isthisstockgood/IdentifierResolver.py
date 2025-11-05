"""Utilities for resolving arbitrary stock identifiers to ticker symbols."""

from __future__ import annotations

import logging
import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib import parse as urlparse, request as urlrequest

try:  # pragma: no cover - optional dependency used in production
  import requests  # type: ignore
except Exception:  # pragma: no cover - fallback to urllib for offline tests
  class _RequestsFallback:
    def get(self, *args, **kwargs):  # pragma: no cover - exercised in tests via monkeypatch
      raise RuntimeError("requests library is not available")

  requests = _RequestsFallback()  # type: ignore

logger = logging.getLogger("IsThisStockGood")

_ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", re.IGNORECASE)
_YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"


@dataclass(frozen=True)
class IdentifierResolution:
    """Represents the result of attempting to resolve an identifier."""

    input_identifier: str
    resolved_symbol: Optional[str]
    identifier_type: str
    successful: bool

    @property
    def symbol(self) -> str:
        """Return the best ticker symbol to use for downstream lookups."""
        if self.resolved_symbol:
            return self.resolved_symbol
        return self.input_identifier


def _is_isin(identifier: str) -> bool:
    """Return True when the supplied identifier looks like an ISIN."""

    if not identifier:
        return False
    return bool(_ISIN_PATTERN.match(identifier.strip()))


def _query_yahoo_finance(identifier: str) -> Optional[str]:
    """Attempt to resolve an identifier to a Yahoo Finance ticker symbol."""

    try:
        if requests is not None:
            response = requests.get(
                _YAHOO_SEARCH_URL,
                params={"q": identifier, "quotesCount": 6, "newsCount": 0},
                timeout=10,
            )
            status_code = response.status_code
            content = response.json()
        else:  # pragma: no cover - exercised in offline tests
            query = urlparse.urlencode({"q": identifier, "quotesCount": 6, "newsCount": 0})
            url = f"{_YAHOO_SEARCH_URL}?{query}"
            with urlrequest.urlopen(url, timeout=10) as raw_response:
                status_code = getattr(raw_response, "status", 200)
                body = raw_response.read().decode("utf-8")
            if status_code != 200:
                logger.warning(
                    "Yahoo Finance search returned non-success status %s for identifier %s",
                    status_code,
                    identifier,
                )
                return None
            content = json.loads(body)
    except Exception:  # pragma: no cover - network errors are logged and ignored.
        logger.exception("Unable to query Yahoo Finance search for identifier %s", identifier)
        return None

    if status_code != 200:
        logger.warning(
            "Yahoo Finance search returned non-success status %s for identifier %s",
            status_code,
            identifier,
        )
        return None

    payload = content

    for quote in payload.get("quotes", []):
        symbol = quote.get("symbol")
        if not symbol:
            continue

        quote_type = quote.get("quoteType")
        if quote_type and quote_type.lower() not in {"equity", "etf"}:
            continue

        return symbol

    return None


def resolve_identifier(identifier: Optional[str]) -> IdentifierResolution:
    """Resolve an arbitrary identifier to a ticker symbol when possible."""

    if identifier is None:
        return IdentifierResolution("", None, "unknown", False)

    identifier = identifier.strip()
    if not identifier:
        return IdentifierResolution("", None, "unknown", False)

    if _is_isin(identifier):
        symbol = _query_yahoo_finance(identifier)
        success = symbol is not None
        return IdentifierResolution(identifier, symbol, "isin", success)

    return IdentifierResolution(identifier, identifier, "ticker", True)
