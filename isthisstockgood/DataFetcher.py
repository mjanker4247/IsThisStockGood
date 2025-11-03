from __future__ import annotations

import logging
import math
import random
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

import isthisstockgood.RuleOneInvestingCalculations as RuleOne
from requests_futures.sessions import FuturesSession
from requests import Response

from isthisstockgood.Active.MSNMoney import MSNMoney
from isthisstockgood.Active.YahooFinance import YahooFinanceAnalysis
from isthisstockgood.Active.YahooFinanceChart import YahooFinanceChart
from isthisstockgood.Active.Zacks import Zacks
from isthisstockgood.IdentifierResolver import resolve_identifier
from isthisstockgood.config import AppConfig

logger = logging.getLogger("IsThisStockGood")

FuturesSessionFactory = Callable[[], FuturesSession]
DEFAULT_USER_AGENTS: Tuple[str, ...] = tuple(AppConfig().user_agents)


def fetch_data_for_ticker_symbol(
    ticker: str,
    *,
    user_agents: Sequence[str] | None = None,
    session_factory: FuturesSessionFactory | None = None,
) -> Optional[Dict[str, Any]]:
    """Fetch and parse all financial data for ``ticker``.

    Args:
        ticker: The identifier that should be resolved into a tradable ticker symbol.
        user_agents: Optional list of user agent strings to randomize outbound requests.
        session_factory: Optional callable that creates ``FuturesSession`` instances.

    Returns:
        A fully-populated dictionary of processed financial metrics for ``ticker`` or
        ``None`` when the ticker cannot be resolved or upstream data sources fail.

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
        user_agents=user_agents,
        session_factory=session_factory,
    )

    # Kick off all remote requests concurrently so downstream parsing happens without
    # blocking on individual endpoints.
    data_fetcher.fetch_msn_money_data()
    data_fetcher.fetch_yahoo_finance_analysis()
    data_fetcher.fetch_zacks_analysis()

    # Ensure every async request has completed before we attempt to read the parsed
    # payloads, mirroring the synchronization semantics of the legacy implementation.
    for rpc in data_fetcher.rpcs:
        rpc.result()

    msn_money = data_fetcher.msn_money
    yahoo_finance_analysis = data_fetcher.yahoo_finance_analysis
    zacks_analysis = data_fetcher.zacks_analysis

    if msn_money is None:
        logger.error("MSN Money data unavailable for ticker %s", resolved_ticker)
        return None

    # NOTE: Some equities—particularly newly listed or thinly covered tickers—do not
    # expose analyst growth rates. Fall back to Zacks data or zero just like before.
    five_year_growth_rate = (
        yahoo_finance_analysis.five_year_growth_rate if yahoo_finance_analysis
        else zacks_analysis.five_year_growth_rate if zacks_analysis
        else 0
    )

    margin_of_safety_price, sticker_price = _calculate_margin_of_safety_price(
        msn_money.equity_growth_rates[-1],
        msn_money.pe_low,
        msn_money.pe_high,
        sum(msn_money.quarterly_eps[-4:]),
        five_year_growth_rate,
    )
    payback_time = _calculate_payback_time(
        msn_money.equity_growth_rates[-1],
        msn_money.last_year_net_income,
        msn_money.market_cap,
        five_year_growth_rate,
    )

    free_cash_flow_per_share = float(msn_money.free_cash_flow[-1])
    computed_free_cash_flow = round(free_cash_flow_per_share * msn_money.shares_outstanding)
    ten_cap_price = 10 * free_cash_flow_per_share

    template_values = {
        "ticker": msn_money.ticker_symbol if msn_money and msn_money.ticker_symbol else resolved_ticker,
        "identifier": resolution.input_identifier,
        "identifier_type": resolution.identifier_type,
        "identifier_resolution_succeeded": resolution.successful,
        "name": msn_money.name if msn_money and msn_money.name else "null",
        "description": msn_money.description if msn_money and msn_money.description else "null",
        "roic": msn_money.roic_averages if msn_money and msn_money.roic_averages else [],
        "eps": msn_money.eps_growth_rates if msn_money and msn_money.eps_growth_rates else [],
        "sales": msn_money.revenue_growth_rates if msn_money and msn_money.revenue_growth_rates else [],
        "equity": msn_money.equity_growth_rates if msn_money and msn_money.equity_growth_rates else [],
        "cash": msn_money.free_cash_flow_growth_rates if msn_money and msn_money.free_cash_flow_growth_rates else [],
        "total_debt": msn_money.total_debt,
        "free_cash_flow": computed_free_cash_flow,
        "ten_cap_price": round(ten_cap_price, 2),
        "debt_payoff_time": round(float(msn_money.total_debt) / computed_free_cash_flow),
        "debt_equity_ratio": msn_money.debt_equity_ratio if msn_money and msn_money.debt_equity_ratio >= 0 else -1,
        "margin_of_safety_price": margin_of_safety_price if margin_of_safety_price else "null",
        "current_price": msn_money.current_price if msn_money and msn_money.current_price else "null",
        "sticker_price": sticker_price if sticker_price else "null",
        "payback_time": payback_time if payback_time else "null",
        "average_volume": msn_money.average_volume if msn_money and msn_money.average_volume else "null",
    }

    return template_values


def _calculate_growth_rate_decimal(analyst_growth_rate: float, current_growth_rate: float) -> float:
    """Convert the lower of the analyst and trailing growth rates into a decimal."""

    growth_rate = min(float(analyst_growth_rate), float(current_growth_rate))
    # Divide the growth rate by 100 to convert from percent to decimal.
    return growth_rate / 100.0


def _calculate_margin_of_safety_price(
    one_year_equity_growth_rate: float,
    pe_low: float,
    pe_high: float,
    ttm_eps: float,
    analyst_five_year_growth_rate: float,
) -> Tuple[Optional[float], Optional[float]]:
    """Compute the Rule #1 margin of safety and sticker price for the current ticker."""

    if not one_year_equity_growth_rate or not pe_low or not pe_high or not ttm_eps or not analyst_five_year_growth_rate:
        return None, None

    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
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
    market_cap: float,
    analyst_five_year_growth_rate: float,
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
    try:
        return RuleOne.payback_time(market_cap, last_year_net_income, growth_rate)
    except ValueError:
        logger.warning(
            "Unable to compute payback time with market cap=%s, income=%s, growth=%s",
            market_cap,
            last_year_net_income,
            growth_rate,
        )
        return None


class DataFetcher:
    """Coordinate asynchronous fetching and parsing for a single ticker symbol."""

    def __init__(
        self,
        ticker: str,
        *,
        user_agents: Sequence[str] | None = None,
        session_factory: FuturesSessionFactory | None = None,
    ) -> None:
        """Initialize a new ``DataFetcher`` instance.

        Args:
            ticker: The resolved ticker symbol to fetch.
            user_agents: Optional list of HTTP user agent strings used for requests.
            session_factory: Optional callable returning a ``FuturesSession``.
        """

        self.rpcs: list[Any] = []
        self.ticker_symbol = ticker
        self.msn_money: Optional[MSNMoney] = None
        self.yahoo_finance_analysis: Optional[YahooFinanceAnalysis] = None
        self.zacks_analysis: Optional[Zacks] = None
        self.yahoo_finance_chart: Optional[YahooFinanceChart] = None
        self.error = False
        agents = tuple(user_agents) if user_agents else DEFAULT_USER_AGENTS
        self._user_agents: Tuple[str, ...] = agents or DEFAULT_USER_AGENTS
        self._session_factory: FuturesSessionFactory = session_factory or FuturesSession
        self._session: FuturesSession | None = None

    def _get_session(self) -> FuturesSession:
        """Return a cached ``FuturesSession`` instance, creating it as needed."""

        if self._session is None:
            self._session = self._session_factory()
        return self._session

    def _schedule_request(
        self,
        url: str,
        *,
        hooks: Mapping[str, Callable[..., Any]] | None = None,
        allow_redirects: bool = True,
    ) -> None:
        """Submit an asynchronous GET request and register the resulting future."""

        session = self._get_session()
        rpc = session.get(
            url,
            allow_redirects=allow_redirects,
            headers={"User-Agent": random.choice(self._user_agents)},
            hooks=hooks,
        )
        self.rpcs.append(rpc)

    def fetch_msn_money_data(self) -> None:
        """Start the asynchronous workflow to download MSN Money datasets."""

        self.msn_money = MSNMoney(self.ticker_symbol)
        self._schedule_request(
            self.msn_money.get_ticker_autocomplete_url(),
            hooks={"response": self.continue_fetching_msn_money_data},
        )

    def continue_fetching_msn_money_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Chain additional MSN Money requests once the stock identifier is known."""

        msn_stock_id = self.msn_money.extract_stock_id(response.text)
        self._schedule_request(
            self.msn_money.get_key_ratios_url(msn_stock_id),
            hooks={"response": self.parse_msn_money_ratios_data},
        )
        self._schedule_request(
            self.msn_money.get_quotes_url(msn_stock_id),
            hooks={"response": self.parse_msn_money_quotes_data},
        )
        self._schedule_request(
            self.msn_money.get_annual_statements_url(msn_stock_id),
            hooks={"response": self.parse_msn_money_annual_statement_data},
        )

    def parse_msn_money_ratios_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse the ratios dataset returned from MSN Money."""

        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_ratios_data(result)

    def parse_msn_money_quotes_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse the quotes dataset returned from MSN Money."""

        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_quotes_data(result)

    def parse_msn_money_annual_statement_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse the annual statement dataset returned from MSN Money."""

        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_annual_report_data(result)

    def fetch_yahoo_finance_analysis(self) -> None:
        """Start the asynchronous Yahoo Finance analyst analysis fetch."""

        self.yahoo_finance_analysis = YahooFinanceAnalysis(self.ticker_symbol)
        self._schedule_request(
            self.yahoo_finance_analysis.url,
            hooks={"response": self.parse_yahoo_finance_analysis},
        )

    def parse_yahoo_finance_analysis(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse Yahoo Finance analyst projections and drop invalid payloads."""

        if response.status_code != 200:
            return
        if not self.yahoo_finance_analysis:
            return
        result = response.text
        success = self.yahoo_finance_analysis.parse_analyst_five_year_growth_rate(result)
        if not success:
            self.yahoo_finance_analysis = None

    def fetch_zacks_analysis(self) -> None:
        """Start the asynchronous Zacks analyst analysis fetch."""

        self.zacks_analysis = Zacks(self.ticker_symbol)

        self._schedule_request(
            self.zacks_analysis.url,
            hooks={"response": self.zacks_analysis.parse},
        )

    def parse_growth_rate_estimate(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse supplemental Zacks growth rate data."""

        if response.status_code != 200:
            return
        if not self.zacks_analysis:
            return
        result = response.text
        success = self.zacks_analysis.parse_analyst_five_year_growth_rate(result)
        if not success:
            self.zacks_analysis = None

    def fetch_yahoo_finance_chart(self) -> None:
        """Start the asynchronous Yahoo Finance chart fetch."""

        self.yahoo_finance_chart = YahooFinanceChart(self.ticker_symbol)
        self._schedule_request(
            self.yahoo_finance_chart.url,
            hooks={"response": self.parse_yahoo_finance_chart},
        )

    def parse_yahoo_finance_chart(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """Parse the historical price chart data from Yahoo Finance."""

        if response.status_code != 200:
            return
        if not self.yahoo_finance_chart:
            return
        result = response.text
        success = self.yahoo_finance_chart.parse_chart(result)
        if not success:
            self.yahoo_finance_chart = None


fetchDataForTickerSymbol = fetch_data_for_ticker_symbol

__all__ = ["fetch_data_for_ticker_symbol", "DataFetcher"]
