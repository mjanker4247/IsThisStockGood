import pytest
from app.FinancialDataFetcher import FinancialDataFetcher
from app.CompanyInfo import CompanyInfo
from app.DataFetcher import fetchDataForTickerSymbol

def test_fetch_summary_data():
    fetcher = FinancialDataFetcher("AAPL")
    data = fetcher.fetch_summary_data()
    assert 'current_price' in data
    assert 'market_cap' in data
    assert data['current_price'] is None or isinstance(data['current_price'], (float, int))

def test_fetch_all():
    fetcher = FinancialDataFetcher("AAPL")
    data = fetcher.fetch_all()
    assert 'current_price' in data
    assert (data['five_year_growth_rate_yahoo'] is None or 
            isinstance(data['five_year_growth_rate_yahoo'], float))

def test_company_info_dataclass():
    company = CompanyInfo(
        tickersymbol="TSLA",
        currentprice=500.0,
        marketcap=800000000000
    )
    assert company.tickersymbol == "TSLA"
    assert company.currentprice == 500.0

def test_fetch_data_for_valid_ticker():
    company_info = fetchDataForTickerSymbol("MSFT")
    assert isinstance(company_info, CompanyInfo)
    assert company_info.tickersymbol == "MSFT"

def test_fetch_data_for_invalid_ticker():
    company_info = fetchDataForTickerSymbol("INVALID")
    assert company_info is None
