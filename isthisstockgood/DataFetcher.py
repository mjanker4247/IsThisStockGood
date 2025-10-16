from __future__ import annotations

import logging
import random
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

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
    """Fetch and parse financial data for ``ticker``."""

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

    data_fetcher.fetch_msn_money_data()
    data_fetcher.fetch_yahoo_finance_analysis()
    data_fetcher.fetch_zacks_analysis()

    for rpc in data_fetcher.rpcs:
        rpc.result()

    msn_money = data_fetcher.msn_money
    yahoo_finance_analysis = data_fetcher.yahoo_finance_analysis
    zacks_analysis = data_fetcher.zacks_analysis

    if msn_money is None:
        logger.error("MSN Money data unavailable for ticker %s", resolved_ticker)
        return None

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
    growth_rate = min(float(analyst_growth_rate), float(current_growth_rate))
    return growth_rate / 100.0


def _calculate_margin_of_safety_price(
    one_year_equity_growth_rate: float,
    pe_low: float,
    pe_high: float,
    ttm_eps: float,
    analyst_five_year_growth_rate: float,
) -> Tuple[Optional[float], Optional[float]]:
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
    if not one_year_equity_growth_rate or not last_year_net_income or not market_cap or not analyst_five_year_growth_rate:
        return None

    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    payback_time = RuleOne.payback_time(market_cap, last_year_net_income, growth_rate)
    return payback_time


class DataFetcher:
    """A helper class that synchronizes all of the async data fetches."""

    def __init__(
        self,
        ticker: str,
        *,
        user_agents: Sequence[str] | None = None,
        session_factory: FuturesSessionFactory | None = None,
    ) -> None:
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

    def _create_session(self) -> FuturesSession:
        session = self._session_factory()
        session.headers.update({"User-Agent": random.choice(self._user_agents)})
        return session

    def fetch_msn_money_data(self) -> None:
        self.msn_money = MSNMoney(self.ticker_symbol)
        session = self._create_session()
        rpc = session.get(
            self.msn_money.get_ticker_autocomplete_url(),
            allow_redirects=True,
            hooks={"response": self.continue_fetching_msn_money_data},
        )
        self.rpcs.append(rpc)

    def continue_fetching_msn_money_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        msn_stock_id = self.msn_money.extract_stock_id(response.text)
        session = self._create_session()
        rpc = session.get(
            self.msn_money.get_key_ratios_url(msn_stock_id),
            allow_redirects=True,
            hooks={"response": self.parse_msn_money_ratios_data},
        )
        self.rpcs.append(rpc)
        rpc = session.get(
            self.msn_money.get_quotes_url(msn_stock_id),
            allow_redirects=True,
            hooks={"response": self.parse_msn_money_quotes_data},
        )
        self.rpcs.append(rpc)
        rpc = session.get(
            self.msn_money.get_annual_statements_url(msn_stock_id),
            allow_redirects=True,
            hooks={"response": self.parse_msn_money_annual_statement_data},
        )
        self.rpcs.append(rpc)

    def parse_msn_money_ratios_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_ratios_data(result)

    def parse_msn_money_quotes_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_quotes_data(result)

    def parse_msn_money_annual_statement_data(self, response: Response, *args: Any, **kwargs: Any) -> None:
        if response.status_code != 200:
            return
        if not self.msn_money:
            return
        result = response.text
        self.msn_money.parse_annual_report_data(result)

    def fetch_yahoo_finance_analysis(self) -> None:
        self.yahoo_finance_analysis = YahooFinanceAnalysis(self.ticker_symbol)
        session = self._create_session()
        rpc = session.get(
            self.yahoo_finance_analysis.url,
            allow_redirects=True,
            hooks={"response": self.parse_yahoo_finance_analysis},
        )
        self.rpcs.append(rpc)

    def parse_yahoo_finance_analysis(self, response: Response, *args: Any, **kwargs: Any) -> None:
        if response.status_code != 200:
            return
        if not self.yahoo_finance_analysis:
            return
        result = response.text
        success = self.yahoo_finance_analysis.parse_analyst_five_year_growth_rate(result)
        if not success:
            self.yahoo_finance_analysis = None

    def fetch_zacks_analysis(self) -> None:
        session = self._create_session()
        self.zacks_analysis = Zacks(self.ticker_symbol)

        rpc = session.get(
            self.zacks_analysis.url,
            allow_redirects=True,
            hooks={"response": self.zacks_analysis.parse},
        )
        self.rpcs.append(rpc)

    def parse_growth_rate_estimate(self, response: Response, *args: Any, **kwargs: Any) -> None:
        if response.status_code != 200:
            return
        if not self.zacks_analysis:
            return
        result = response.text
        success = self.zacks_analysis.parse_analyst_five_year_growth_rate(result)
        if not success:
            self.zacks_analysis = None

    def fetch_yahoo_finance_chart(self) -> None:
        self.yahoo_finance_chart = YahooFinanceChart(self.ticker_symbol)
        session = self._create_session()
        rpc = session.get(
            self.yahoo_finance_chart.url,
            allow_redirects=True,
            hooks={"response": self.parse_yahoo_finance_chart},
        )
        self.rpcs.append(rpc)

    def parse_yahoo_finance_chart(self, response: Response, *args: Any, **kwargs: Any) -> None:
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
