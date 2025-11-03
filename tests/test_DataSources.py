import json

import pytest

from isthisstockgood.DataFetcher import DataFetcher
from isthisstockgood.Active.MSNMoney import MSNMoney, _compute_growth_rates_for_data


def test_msn_money_parsing(offline_data_fetcher):
    offline_data_fetcher()
    fetcher = DataFetcher("MSFT")
    fetcher.fetch_msn_money_data()

    assert fetcher.msn_money is not None
    msn = fetcher.msn_money

    assert msn.ticker_symbol == "MSFT"
    assert msn.name == "Microsoft Corporation"
    assert msn.description.startswith("Microsoft Corporation provides")
    assert msn.industry == "Software"
    assert msn.current_price == 330.12
    assert msn.average_volume == 25_000_000
    assert msn.market_cap == 2_450_000_000_000
    assert msn.shares_outstanding == 7_500_000_000
    assert msn.pe_high == 24.5
    assert msn.pe_low == 18.5
    assert msn.debt_equity_ratio == 0.435
    assert msn.total_debt == 65_000_000_000
    assert msn.quarterly_eps[-4:] == [1.6, 1.7, 1.75, 1.8]
    assert msn.last_year_net_income == sum(msn.quarterly_eps[-4:]) * msn.shares_outstanding


def test_future_growth_rates(offline_data_fetcher):
    offline_data_fetcher()
    fetcher = DataFetcher("MSFT")
    fetcher.fetch_yahoo_finance_analysis()
    fetcher.fetch_zacks_analysis()

    assert fetcher.yahoo_finance_analysis is not None
    assert fetcher.yahoo_finance_analysis.five_year_growth_rate == "18.0"
    assert fetcher.zacks_analysis is not None
    assert fetcher.zacks_analysis.five_year_growth_rate == 17.5


def test_growth_rates_ignore_opposing_signs(caplog):
    caplog.set_level("DEBUG", logger="IsThisStockGood")

    data_points = [-1.5, 2.0]

    growth_rates = _compute_growth_rates_for_data(data_points)

    assert growth_rates == []
    assert any(
        "Skipping CAGR calculation" in message
        for message in (record.message for record in caplog.records)
    )


def _build_minimal_key_ratios_payload() -> str:
    annual_metrics = []
    for idx in range(6):
        annual_metrics.append(
            {
                "fiscalPeriodType": "Annual",
                "earningsPerShare": 1.0 + idx,
                "freeCashFlowPerShare": 2.0 + idx,
                "bookValuePerShare": 3.0 + idx,
                "revenuePerShare": 4.0 + idx,
                "roic": 10 + idx,
                "priceToEarningsRatio": 15 + idx,
            }
        )

    quarterly_eps = [0.5, 0.6, 0.7, 0.8]
    quarterly_metrics = []
    for idx, eps in enumerate(quarterly_eps, start=1):
        quarterly_metrics.append(
            {
                "fiscalPeriodType": f"Q{idx}",
                "earningsPerShare": eps,
                "debtToEquityRatio": 40 + idx,
            }
        )

    payload = {
        "displayName": "Test Corp",
        "industry": "Testing",
        "companyMetrics": annual_metrics + quarterly_metrics,
    }
    return json.dumps(payload)


def test_last_year_net_income_requires_shares_outstanding():
    payload = _build_minimal_key_ratios_payload()
    msn = MSNMoney("TEST")

    assert msn.parse_ratios_data(payload)
    assert msn.last_year_net_income is None

    msn.shares_outstanding = "1000"
    assert msn.parse_ratios_data(payload)
    assert pytest.approx(sum(msn.quarterly_eps[-4:]) * 1000) == msn.last_year_net_income
