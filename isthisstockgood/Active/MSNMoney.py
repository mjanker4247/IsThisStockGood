"""Company fundamentals built from yfinance and Alpha Vantage."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from isthisstockgood.Active.alphavantage_client import AlphaVantageFundamentals, AlphaVantageError
from isthisstockgood.Active.yfinance_client import YFinanceCompanyProfile

logger = logging.getLogger("IsThisStockGood")


class MSNMoneyError(RuntimeError):
    """Raised when market data cannot be populated."""


@dataclass
class MSNMoney:
    """Aggregate company fundamentals required by the application."""

    ticker_symbol: str
    alpha_vantage_api_key: str | None = None
    yfinance_loader: Callable[[str], object] | None = None

    name: str = ""
    description: str = ""
    industry: str = ""
    current_price: float | None = None
    average_volume: float | None = None
    market_cap: float | None = None
    shares_outstanding: float = 0.0
    pe_high: float | None = None
    pe_low: float | None = None
    roic: list[float] = field(default_factory=list)
    roic_averages: list[float] | None = None
    equity: list[float] = field(default_factory=list)
    equity_growth_rates: list[float] | None = None
    free_cash_flow: list[float] = field(default_factory=list)
    free_cash_flow_growth_rates: list[float] | None = None
    revenue: list[float] = field(default_factory=list)
    revenue_growth_rates: list[float] | None = None
    eps: list[float] = field(default_factory=list)
    eps_growth_rates: list[float] | None = None
    debt_equity_ratio: float = -1.0
    last_year_net_income: float = 0.0
    total_debt: float = 0.0
    quarterly_eps: list[float] = field(default_factory=list)
    five_year_growth_rate: float | None = None
    trailing_twelve_month_eps: float = 0.0

    def load(self) -> None:
        if not self.alpha_vantage_api_key:
            raise MSNMoneyError("Alpha Vantage API key is required")

        profile = YFinanceCompanyProfile(self.ticker_symbol, ticker_loader=self.yfinance_loader)
        try:
            profile.fetch()
        except Exception as exc:  # pragma: no cover - network failure
            raise MSNMoneyError(f"Unable to load yfinance data: {exc}") from exc

        fundamentals = AlphaVantageFundamentals(
            self.ticker_symbol,
            api_key=self.alpha_vantage_api_key,
            shares_outstanding_override=profile.shares_outstanding,
        )
        try:
            fundamentals.fetch()
        except (AlphaVantageError, Exception) as exc:  # pragma: no cover - network failure
            raise MSNMoneyError(f"Unable to load Alpha Vantage data: {exc}") from exc

        self._apply_sources(profile, fundamentals)

    def _apply_sources(
        self,
        profile: YFinanceCompanyProfile,
        fundamentals: AlphaVantageFundamentals,
    ) -> None:
        self.ticker_symbol = profile.ticker_symbol
        self.name = profile.name
        self.description = profile.description
        self.industry = profile.industry
        self.current_price = profile.current_price
        self.average_volume = profile.average_volume
        self.market_cap = profile.market_cap
        self.shares_outstanding = float(fundamentals.shares_outstanding or profile.shares_outstanding or 0.0)

        pe_high, pe_low = profile.compute_pe_range(fundamentals.annual_eps_map)
        self.pe_high = pe_high
        self.pe_low = pe_low

        self.roic = fundamentals.roic
        self.roic_averages = fundamentals.roic_averages
        self.equity = fundamentals.equity_per_share
        self.equity_growth_rates = fundamentals.equity_growth_rates
        self.free_cash_flow = fundamentals.free_cash_flow_per_share
        self.free_cash_flow_growth_rates = fundamentals.free_cash_flow_growth_rates
        self.revenue = fundamentals.revenue_per_share
        self.revenue_growth_rates = fundamentals.revenue_growth_rates
        self.eps = fundamentals.eps
        self.eps_growth_rates = fundamentals.eps_growth_rates
        self.debt_equity_ratio = fundamentals.debt_equity_ratio
        self.last_year_net_income = fundamentals.last_year_net_income
        self.total_debt = fundamentals.total_debt
        self.quarterly_eps = fundamentals.quarterly_eps
        self.five_year_growth_rate = fundamentals.five_year_growth_rate
        self.trailing_twelve_month_eps = fundamentals.trailing_twelve_month_eps

    @classmethod
    def from_sources(
        cls,
        ticker_symbol: str,
        *,
        profile: YFinanceCompanyProfile,
        fundamentals: AlphaVantageFundamentals,
    ) -> "MSNMoney":
        instance = cls(ticker_symbol)
        instance._apply_sources(profile, fundamentals)
        return instance


__all__ = ["MSNMoney", "MSNMoneyError"]
