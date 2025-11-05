"""Utilities for retrieving company profiles via :mod:`yfinance`."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, Iterable, Mapping, MutableMapping, Optional

try:  # pragma: no cover - optional dependency is exercised in integration tests
    import yfinance as yf
except Exception:  # pragma: no cover - defer import errors to runtime usage
    yf = None

logger = logging.getLogger("IsThisStockGood")


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_year(date_value: object) -> Optional[int]:
    if isinstance(date_value, datetime):
        return date_value.year
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value).year
        except ValueError:
            try:
                return datetime.strptime(date_value, "%Y-%m-%d").year
            except ValueError:
                return None
    return None


@dataclass
class YFinanceCompanyProfile:
    """Representation of the descriptive data returned by :mod:`yfinance`."""

    ticker_symbol: str
    ticker_loader: Callable[[str], object] | None = None

    name: str = ""
    description: str = ""
    industry: str = ""
    current_price: float | None = None
    average_volume: float | None = None
    market_cap: float | None = None
    shares_outstanding: float | None = None
    year_end_closes: MutableMapping[int, float] = field(default_factory=dict)

    def fetch(self) -> None:
        """Populate the profile using :mod:`yfinance`."""

        if self.ticker_loader is not None:
            ticker = self.ticker_loader(self.ticker_symbol)
        else:
            if yf is None:  # pragma: no cover - real import error surfaced at runtime
                raise RuntimeError("yfinance is not installed")
            ticker = yf.Ticker(self.ticker_symbol)

        info = getattr(ticker, "info", {}) or {}
        fast_info = getattr(ticker, "fast_info", {}) or {}

        self._apply_metadata(info, fast_info)
        self._apply_history(ticker)

    def _apply_metadata(self, info: Mapping[str, object], fast_info: Mapping[str, object]) -> None:
        self.name = str(info.get("longName") or info.get("shortName") or "")
        self.description = str(info.get("longBusinessSummary") or "")
        self.industry = str(info.get("industry") or "")

        price = _safe_float(fast_info.get("last_price"))
        if price is None:
            price = _safe_float(info.get("regularMarketPrice"))
        self.current_price = price

        volume = (
            _safe_float(info.get("averageDailyVolume3Month"))
            or _safe_float(info.get("averageVolume"))
        )
        self.average_volume = volume

        market_cap = _safe_float(fast_info.get("market_cap"))
        if market_cap is None:
            market_cap = _safe_float(info.get("marketCap"))
        self.market_cap = market_cap

        shares = _safe_float(info.get("sharesOutstanding"))
        if shares is None:
            shares = _safe_float(fast_info.get("shares_outstanding"))
        self.shares_outstanding = shares

    def _apply_history(self, ticker: object) -> None:
        history = None
        if hasattr(ticker, "history"):
            try:
                history = ticker.history(period="6y", interval="1mo")
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Unable to load price history via yfinance: %s", exc)

        if history is None or getattr(history, "empty", False):
            return

        closes: Iterable[tuple[object, object]]
        if hasattr(history, "iterrows"):
            closes = ((index, row.get("Close")) for index, row in history.iterrows())
        elif isinstance(history, Mapping):
            closes = history.items()
        else:
            closes = history  # type: ignore[assignment]

        grouped: Dict[int, float] = {}
        for index, value in closes:
            raw_index = index.to_pydatetime() if hasattr(index, "to_pydatetime") else index
            year = _parse_year(raw_index)
            close_price = _safe_float(value.get("Close") if isinstance(value, Mapping) else value)
            if year is None or close_price is None:
                continue
            grouped[year] = close_price

        if grouped:
            self.year_end_closes = dict(sorted(grouped.items()))

    def compute_pe_range(self, annual_eps: Mapping[int, float] | Mapping[str, float]) -> tuple[Optional[float], Optional[float]]:
        """Compute historical P/E bounds from the recorded closes and EPS data."""

        if not self.year_end_closes or not annual_eps:
            return None, None

        ratios = []
        for year, price in self.year_end_closes.items():
            eps_value = annual_eps.get(year)
            if eps_value is None:
                eps_value = annual_eps.get(str(year))
            eps_float = _safe_float(eps_value)
            if eps_float is None or eps_float == 0:
                continue
            ratios.append(round(price / eps_float, 2))

        if not ratios:
            return None, None

        return max(ratios), min(ratios)

    @classmethod
    def from_payload(cls, ticker_symbol: str, payload: Mapping[str, object]) -> "YFinanceCompanyProfile":
        instance = cls(ticker_symbol)
        info = payload.get("info", {}) if isinstance(payload, Mapping) else {}
        fast_info = payload.get("fast_info", {}) if isinstance(payload, Mapping) else {}
        history = payload.get("history") if isinstance(payload, Mapping) else None

        instance._apply_metadata(info, fast_info)
        if isinstance(history, Iterable):
            closes: Dict[int, float] = {}
            for entry in history:
                if not isinstance(entry, Mapping):
                    continue
                year = _parse_year(entry.get("date"))
                close_price = _safe_float(entry.get("close"))
                if year is None or close_price is None:
                    continue
                closes[year] = close_price
            instance.year_end_closes = dict(sorted(closes.items()))
        return instance


__all__ = ["YFinanceCompanyProfile"]
