"""Integration helpers for the Alpha Vantage fundamentals API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Mapping, Optional
from urllib import parse as urlparse, request as urlrequest

try:  # pragma: no cover - optional dependency used in production
    import requests  # type: ignore
except Exception:  # pragma: no cover - fallback to urllib for offline tests
    requests = None  # type: ignore


class _FallbackSession:
    """Minimal session compatible with :func:`_get_json` when requests is unavailable."""

    def close(self) -> None:  # pragma: no cover - no resources to release
        return None


def _default_session_factory() -> object:
    if requests is not None:
        return requests.Session()  # type: ignore[no-any-return]
    return _FallbackSession()

import isthisstockgood.RuleOneInvestingCalculations as RuleOne

logger = logging.getLogger("IsThisStockGood")


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_year(value: str | int | None) -> Optional[int]:
    if isinstance(value, int):
        return value
    if not value:
        return None
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def _compute_growth_rates_for_data(data: Iterable[float]) -> list[float] | None:
    values = [float(entry) for entry in data if entry is not None]
    if len(values) < 2:
        return None

    results: list[float] = []
    try:
        results.append(RuleOne.compound_annual_growth_rate(values[-2], values[-1], 1))
        if len(values) > 3:
            results.append(RuleOne.compound_annual_growth_rate(values[-4], values[-1], 3))
        if len(values) > 5:
            results.append(RuleOne.compound_annual_growth_rate(values[-6], values[-1], 5))
        if len(values) > 6:
            results.append(
                RuleOne.compound_annual_growth_rate(values[0], values[-1], len(values) - 1)
            )
    except ValueError:
        logger.debug("Failed to compute growth rate for data: %s", values, exc_info=True)
        return None

    return results or None


def _compute_averages_for_data(data: Iterable[float]) -> list[float] | None:
    values = [float(entry) for entry in data if entry is not None]
    if not values:
        return None

    windows = [1, 3, 5, len(values)]
    results: list[float] = []
    for window in windows:
        if len(values) >= window:
            window_values = values[-window:]
            results.append(round(sum(window_values) / len(window_values), 2))
    deduped: list[float] = []
    for entry in results:
        if entry not in deduped:
            deduped.append(entry)
    return deduped


class AlphaVantageError(RuntimeError):
    """Raised when the Alpha Vantage API returns an error payload."""


@dataclass
class AlphaVantageFundamentals:
    ticker_symbol: str
    api_key: str
    base_url: str = "https://www.alphavantage.co/query"
    session_factory: Callable[[], object] | None = None
    shares_outstanding_override: float | None = None

    shares_outstanding: float = 0.0
    total_debt: float = 0.0
    debt_equity_ratio: float = -1.0
    last_year_net_income: float = 0.0
    quarterly_eps: list[float] = field(default_factory=list)
    eps: list[float] = field(default_factory=list)
    revenue_per_share: list[float] = field(default_factory=list)
    equity_per_share: list[float] = field(default_factory=list)
    free_cash_flow_per_share: list[float] = field(default_factory=list)
    roic: list[float] = field(default_factory=list)
    eps_growth_rates: list[float] | None = None
    revenue_growth_rates: list[float] | None = None
    equity_growth_rates: list[float] | None = None
    free_cash_flow_growth_rates: list[float] | None = None
    roic_averages: list[float] | None = None
    five_year_growth_rate: float | None = None
    trailing_twelve_month_eps: float = 0.0
    annual_eps_map: Dict[int, float] = field(default_factory=dict)

    def fetch(self) -> None:
        if not self.api_key:
            raise AlphaVantageError("Alpha Vantage API key is required")

        session_factory = self.session_factory or _default_session_factory
        session = session_factory()
        try:
            overview = self._get_json(session, "OVERVIEW")
            income = self._get_json(session, "INCOME_STATEMENT")
            balance = self._get_json(session, "BALANCE_SHEET")
            cash_flow = self._get_json(session, "CASH_FLOW")
            earnings = self._get_json(session, "EARNINGS")
        finally:
            session.close()

        self._populate_from_payload(overview, income, balance, cash_flow, earnings)

    def _get_json(self, session: object, function: str) -> Mapping[str, object]:
        params = {"function": function, "symbol": self.ticker_symbol, "apikey": self.api_key}
        if requests and isinstance(session, requests.Session):  # type: ignore[attr-defined]
            response = session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        else:  # pragma: no cover - exercised in offline tests
            query = urlparse.urlencode(params)
            url = f"{self.base_url}?{query}"
            with urlrequest.urlopen(url, timeout=30) as raw_response:
                status = getattr(raw_response, "status", 200)
                if not 200 <= status < 400:
                    raise AlphaVantageError(f"HTTP {status}")
                payload = json.loads(raw_response.read().decode("utf-8"))
        if "Error Message" in payload or "Note" in payload:
            raise AlphaVantageError(payload.get("Error Message") or payload.get("Note") or "Unknown error")
        return payload

    def _populate_from_payload(
        self,
        overview: Mapping[str, object],
        income: Mapping[str, object],
        balance: Mapping[str, object],
        cash_flow: Mapping[str, object],
        earnings: Mapping[str, object],
    ) -> None:
        shares = _safe_float(overview.get("SharesOutstanding")) or self.shares_outstanding_override
        if shares:
            self.shares_outstanding = float(shares)
        else:
            self.shares_outstanding = 0.0

        income_reports = self._index_reports(income.get("annualReports"))
        balance_reports = self._index_reports(balance.get("annualReports"))
        cash_flow_reports = self._index_reports(cash_flow.get("annualReports"))
        annual_eps = self._index_reports(earnings.get("annualEarnings"), value_key="reportedEPS")

        if annual_eps:
            self.annual_eps_map = {year: float(value) for year, value in annual_eps.items() if value is not None}
            eps_values = [value for _, value in sorted(self.annual_eps_map.items())]
            self.eps = eps_values
            if len(eps_values) >= 6:
                try:
                    self.five_year_growth_rate = RuleOne.compound_annual_growth_rate(
                        eps_values[-6], eps_values[-1], 5
                    )
                except ValueError:
                    self.five_year_growth_rate = None
            self.eps_growth_rates = _compute_growth_rates_for_data(eps_values) or None

        years = sorted(set(income_reports) & set(balance_reports) & set(cash_flow_reports))
        equity_values: list[float] = []
        revenue_values: list[float] = []
        fcf_values: list[float] = []
        roic_values: list[float] = []

        for year in years:
            income_report = income_reports.get(year)
            balance_report = balance_reports.get(year)
            cash_flow_report = cash_flow_reports.get(year)

            if not (
                isinstance(income_report, Mapping)
                and isinstance(balance_report, Mapping)
                and isinstance(cash_flow_report, Mapping)
            ):
                continue

            revenue = _safe_float(income_report.get("totalRevenue")) or 0.0
            net_income = _safe_float(income_report.get("netIncome")) or 0.0
            ebit = _safe_float(income_report.get("ebit")) or net_income
            equity = _safe_float(balance_report.get("totalShareholderEquity")) or 0.0
            debt = _safe_float(balance_report.get("totalDebt")) or 0.0
            cash_on_hand = _safe_float(
                balance_report.get("cashAndCashEquivalentsAtCarryingValue")
            ) or 0.0
            operating_cashflow = _safe_float(cash_flow_report.get("operatingCashflow")) or 0.0
            capital_expenditures = _safe_float(cash_flow_report.get("capitalExpenditures")) or 0.0

            if year == max(years):
                self.total_debt = debt
                self.last_year_net_income = net_income
                if equity > 0:
                    self.debt_equity_ratio = round(debt / equity, 3)

            if self.shares_outstanding > 0:
                revenue_values.append(revenue / self.shares_outstanding)
                equity_values.append(equity / self.shares_outstanding)
                free_cash_flow = operating_cashflow + capital_expenditures
                fcf_values.append(free_cash_flow / self.shares_outstanding)

            invested_capital = equity + debt - cash_on_hand
            if invested_capital > 0:
                roic_values.append(round((ebit / invested_capital) * 100, 2))

        self.revenue_per_share = revenue_values
        self.equity_per_share = equity_values
        self.free_cash_flow_per_share = fcf_values
        self.roic = roic_values

        self.revenue_growth_rates = _compute_growth_rates_for_data(revenue_values) or None
        self.equity_growth_rates = _compute_growth_rates_for_data(equity_values) or None
        self.free_cash_flow_growth_rates = _compute_growth_rates_for_data(fcf_values) or None
        self.roic_averages = _compute_averages_for_data(roic_values)

        quarterly_entries = earnings.get("quarterlyEarnings")
        if isinstance(quarterly_entries, Iterable):
            parsed_quarterly: list[tuple[str, float]] = []
            for entry in quarterly_entries:
                if not isinstance(entry, Mapping):
                    continue
                eps_value = _safe_float(entry.get("reportedEPS"))
                period = entry.get("fiscalDateEnding")
                if eps_value is None or period is None:
                    continue
                parsed_quarterly.append((str(period), float(eps_value)))
            parsed_quarterly.sort(key=lambda item: item[0])
            if parsed_quarterly:
                quarterly_values = [value for _, value in parsed_quarterly][-4:]
                self.quarterly_eps = quarterly_values
                self.trailing_twelve_month_eps = sum(quarterly_values)

    def _index_reports(self, reports: object, value_key: str | None = None) -> Dict[int, object]:
        indexed: Dict[int, object] = {}
        if not isinstance(reports, Iterable):
            return indexed
        for entry in reports:
            if not isinstance(entry, Mapping):
                continue
            year = _coerce_year(entry.get("fiscalDateEnding"))
            if year is None:
                continue
            value: object
            if value_key:
                numeric_value = _safe_float(entry.get(value_key))
                if numeric_value is None:
                    continue
                value = numeric_value
            else:
                value = dict(entry)
            indexed[year] = value
        return indexed

    @classmethod
    def from_payload(
        cls,
        ticker_symbol: str,
        *,
        overview: Mapping[str, object],
        income_statement: Mapping[str, object],
        balance_sheet: Mapping[str, object],
        cash_flow: Mapping[str, object],
        earnings: Mapping[str, object],
        shares_override: float | None = None,
    ) -> "AlphaVantageFundamentals":
        instance = cls(
            ticker_symbol,
            api_key="offline",
            shares_outstanding_override=shares_override,
        )
        instance._populate_from_payload(overview, income_statement, balance_sheet, cash_flow, earnings)
        return instance


__all__ = ["AlphaVantageFundamentals", "AlphaVantageError"]
