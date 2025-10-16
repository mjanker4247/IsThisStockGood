from isthisstockgood.DataFetcher import DataFetcher


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
