"""High-level coordination for fetching company fundamentals."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence

import isthisstockgood.RuleOneInvestingCalculations as RuleOne

from isthisstockgood.Active.MSNMoney import MSNMoney, MSNMoneyError
from isthisstockgood.IdentifierResolver import resolve_identifier
from isthisstockgood.config import AppConfig

logger = logging.getLogger("IsThisStockGood")


def fetch_data_for_ticker_symbol(
    ticker: str,
    *,
    user_agents: Sequence[str] | None = None,  # retained for API compatibility
    http_client_factory: Any | None = None,
    executor: Any | None = None,
    alpha_vantage_api_key: str | None = None,
) -> Optional[Dict[str, Any]]:
    """Fetch and parse all financial data for ``ticker``.

    The resulting dictionary mirrors the structure used in the original implementation
    so templates and clients can continue to rely on keys such as ``roic``, ``eps``,
    ``equity``, ``margin_of_safety_price``, ``ten_cap_price``, and ``payback_time``.
    """

    if not ticker:
        return None

    resolution = resolve_identifier(ticker)
    if resolution.identifier_type == "isin" and not resolution.successful:
        logger.warning("Unable to resolve ISIN %s to a ticker symbol", ticker)
        return None

    resolved_ticker = resolution.symbol

    data_fetcher = DataFetcher(
        resolved_ticker,
        alpha_vantage_api_key=alpha_vantage_api_key,
    )

    try:
        data_fetcher.fetch_msn_money_data()
        data_fetcher.flush()
        fundamentals = data_fetcher.msn_money
    finally:
        data_fetcher.close()

    if fundamentals is None:
        logger.error("Fundamental data unavailable for ticker %s", resolved_ticker)
        return None

    five_year_growth_rate = fundamentals.five_year_growth_rate or 0.0
    equity_growth_rates = fundamentals.equity_growth_rates or []
    one_year_equity_growth = equity_growth_rates[-1] if equity_growth_rates else 0.0

    ttm_eps = fundamentals.trailing_twelve_month_eps or sum(fundamentals.quarterly_eps[-4:])

    margin_of_safety_price, sticker_price = _calculate_margin_of_safety_price(
        one_year_equity_growth,
        fundamentals.pe_low,
        fundamentals.pe_high,
        ttm_eps,
        five_year_growth_rate,
    )
    payback_time = _calculate_payback_time(
        one_year_equity_growth,
        fundamentals.last_year_net_income,
        fundamentals.market_cap,
        five_year_growth_rate,
    )

    free_cash_flow_per_share = float(fundamentals.free_cash_flow[-1]) if fundamentals.free_cash_flow else 0.0
    shares_outstanding = fundamentals.shares_outstanding
    computed_free_cash_flow = (
        round(free_cash_flow_per_share * shares_outstanding) if shares_outstanding and free_cash_flow_per_share else 0
    )
    ten_cap_price = 10 * free_cash_flow_per_share if free_cash_flow_per_share else 0.0

    debt_payoff_time: Optional[int]
    if computed_free_cash_flow > 0:
        debt_payoff_time = round(float(fundamentals.total_debt) / computed_free_cash_flow)
    else:
        debt_payoff_time = None

    template_values = {
        "ticker": fundamentals.ticker_symbol or resolved_ticker,
        "identifier": resolution.input_identifier,
        "identifier_type": resolution.identifier_type,
        "identifier_resolution_succeeded": resolution.successful,
        "name": fundamentals.name or "null",
        "description": fundamentals.description or "null",
        "roic": fundamentals.roic_averages or [],
        "eps": fundamentals.eps_growth_rates or [],
        "sales": fundamentals.revenue_growth_rates or [],
        "equity": fundamentals.equity_growth_rates or [],
        "cash": fundamentals.free_cash_flow_growth_rates or [],
        "total_debt": fundamentals.total_debt,
        "free_cash_flow": computed_free_cash_flow,
        "ten_cap_price": round(ten_cap_price, 2),
        "debt_payoff_time": debt_payoff_time,
        "debt_equity_ratio": fundamentals.debt_equity_ratio if fundamentals.debt_equity_ratio >= 0 else -1,
        "margin_of_safety_price": margin_of_safety_price if margin_of_safety_price else "null",
        "current_price": fundamentals.current_price if fundamentals.current_price else "null",
        "sticker_price": sticker_price if sticker_price else "null",
        "payback_time": payback_time if payback_time else "null",
        "average_volume": fundamentals.average_volume if fundamentals.average_volume else "null",
    }

    return template_values


def _calculate_growth_rate_decimal(analyst_growth_rate: float, current_growth_rate: float) -> float:
    """Convert the lower of the analyst and trailing growth rates into a decimal."""

    growth_rate = min(float(analyst_growth_rate or 0), float(current_growth_rate or 0))
    return max(growth_rate, 0.0) / 100.0


def _calculate_margin_of_safety_price(
    one_year_equity_growth_rate: float,
    pe_low: float | None,
    pe_high: float | None,
    ttm_eps: float | None,
    analyst_five_year_growth_rate: float | None,
) -> tuple[Optional[float], Optional[float]]:
    """Compute the Rule #1 margin of safety and sticker price for the current ticker."""

    if not one_year_equity_growth_rate or not pe_low or not pe_high or not ttm_eps or not analyst_five_year_growth_rate:
        return None, None

    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    if growth_rate <= 0:
        return None, None

    margin_of_safety_price, sticker_price = RuleOne.margin_of_safety_price(
        float(ttm_eps),
        growth_rate,
        float(pe_low),
        float(pe_high),
    )
    return margin_of_safety_price, sticker_price


def _calculate_payback_time(
    one_year_equity_growth_rate: float,
    last_year_net_income: float,
    market_cap: float | None,
    analyst_five_year_growth_rate: float | None,
) -> Optional[float]:
    """Estimate the payback time for the equity using Rule #1 methodology."""

    def _is_missing(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, float):
            return math.isnan(value)
        if isinstance(value, int):
            return False
        if isinstance(value, str):
            return not value.strip()
        return False

    if any(
        _is_missing(value)
        for value in (
            one_year_equity_growth_rate,
            last_year_net_income,
            market_cap,
            analyst_five_year_growth_rate,
        )
    ):
        return None

    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    if growth_rate <= 0:
        return None
    try:
        return RuleOne.payback_time(float(market_cap), last_year_net_income, growth_rate)
    except ValueError:
        logger.warning(
            "Unable to compute payback time with market cap=%s, income=%s, growth=%s",
            market_cap,
            last_year_net_income,
            growth_rate,
        )
        return None


@dataclass
class DataFetcher:
    """Coordinate fundamental data retrieval for a single ticker symbol."""

    ticker_symbol: str
    alpha_vantage_api_key: str | None = None
    fundamentals_factory: Callable[[str], MSNMoney] | None = None

    msn_money: Optional[MSNMoney] = None

    def __post_init__(self) -> None:
        if self.alpha_vantage_api_key is None:
            config = AppConfig()
            self.alpha_vantage_api_key = getattr(config, "alpha_vantage_api_key", None)

        if self.fundamentals_factory is None:
            self.fundamentals_factory = self._default_fundamentals_factory

    def _default_fundamentals_factory(self, symbol: str) -> MSNMoney:
        return MSNMoney(symbol, alpha_vantage_api_key=self.alpha_vantage_api_key)

    def fetch_msn_money_data(self) -> None:
        try:
            fundamentals = self.fundamentals_factory(self.ticker_symbol)
            if hasattr(fundamentals, "load"):
                fundamentals.load()
        except MSNMoneyError as exc:
            logger.warning("Failed to load fundamentals for %s: %s", self.ticker_symbol, exc)
            self.msn_money = None
        else:
            self.msn_money = fundamentals

    def flush(self) -> None:  # retained for API compatibility
        return None

    def close(self) -> None:  # retained for API compatibility
        return None


fetchDataForTickerSymbol = fetch_data_for_ticker_symbol

__all__ = ["fetch_data_for_ticker_symbol", "DataFetcher"]
