import pytest

from isthisstockgood.DataFetcher import DataFetcher


def test_company_fundamentals_from_modern_sources(offline_data_fetcher):
    offline_data_fetcher()
    fetcher = DataFetcher("MSFT")
    fetcher.fetch_msn_money_data()

    msn = fetcher.msn_money
    assert msn is not None
    assert msn.ticker_symbol == "MSFT"
    assert msn.name == "Microsoft Corporation"
    assert msn.description.startswith("Microsoft Corporation provides")
    assert msn.industry == "Software"
    assert msn.current_price == pytest.approx(330.12)
    assert msn.average_volume == pytest.approx(25_000_000)
    assert msn.market_cap == pytest.approx(2_450_000_000_000)
    assert msn.shares_outstanding == pytest.approx(7_500_000_000)
    assert msn.pe_high == pytest.approx(36.33, rel=1e-4)
    assert msn.pe_low == pytest.approx(26.19, rel=1e-4)
    assert msn.debt_equity_ratio == pytest.approx(0.31, rel=1e-3)
    assert msn.total_debt == pytest.approx(65_000_000_000)
    assert msn.quarterly_eps[-4:] == pytest.approx([2.09, 2.27, 2.32, 2.45])
    assert msn.last_year_net_income == pytest.approx(72_000_000_000)
    assert msn.five_year_growth_rate == pytest.approx(18.83, rel=1e-3)
    assert msn.trailing_twelve_month_eps == pytest.approx(9.13, rel=1e-3)

    assert msn.eps_growth_rates == pytest.approx([8.03, 10.62, 18.83], rel=1e-3)
    assert msn.equity_growth_rates == pytest.approx([7.69, 8.37, 10.07], rel=1e-3)
    assert msn.free_cash_flow_growth_rates == pytest.approx([6.15, 11.33, 15.9], rel=1e-3)
    assert msn.roic_averages == pytest.approx([35.42, 35.25, 32.66, 30.96], rel=1e-3)


def test_unknown_ticker_returns_no_data(offline_data_fetcher):
    offline_data_fetcher()
    fetcher = DataFetcher("UNKNOWN")
    fetcher.fetch_msn_money_data()

    assert fetcher.msn_money is None
