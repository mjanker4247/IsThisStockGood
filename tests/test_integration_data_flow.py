import pytest

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol


def test_fetch_data_for_ticker_symbol_happy_path(offline_data_fetcher):
    offline_data_fetcher()
    result = fetch_data_for_ticker_symbol('msft')

    assert result is not None
    assert result['ticker'] == 'MSFT'
    assert result['identifier'] == 'msft'
    assert result['identifier_resolution_succeeded'] is True
    assert result['ten_cap_price'] == pytest.approx(52.0)
    assert result['margin_of_safety_price'] == pytest.approx(21.27928049415012, rel=1e-6)
    assert result['payback_time'] == 22
    assert result['free_cash_flow'] == 39_000_000_000
    assert result['debt_equity_ratio'] == pytest.approx(0.435)
    assert result['roic'] == [36.7, 35.1, 33.46]


def test_fetch_data_for_ticker_symbol_returns_none_for_empty_ticker():
    assert fetch_data_for_ticker_symbol('') is None
