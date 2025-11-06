# test_DataSources.py - Updated for yfinance implementation

import pytest
from isthisstockgood.DataFetcher import fetchDataForTickerSymbol
from isthisstockgood.YFinanceData import YFinanceData


def test_yfinance_data_fetcher():
    """
    Test that fetchDataForTickerSymbol returns all required data using yfinance.
    This replaces the old test_msn_money() test.
    """
    test_ticker = 'MSFT'
    
    # Fetch data using the new yfinance implementation
    data = fetchDataForTickerSymbol(test_ticker)
    
    # Verify data is returned (not None)
    assert data is not None, "fetchDataForTickerSymbol should return data"
    
    # Verify it returns a dictionary
    assert isinstance(data, dict), "fetchDataForTickerSymbol should return a dictionary"
    
    # Verify ticker symbol
    assert data['ticker'] == test_ticker
    
    # Verify company name (may vary slightly from 'Microsoft Corp')
    assert data['name'] is not None
    assert 'Microsoft' in data['name']
    
    # Verify basic company info
    assert data['description'] != ''
    assert data['description'] != 'null'
    
    # Verify current price data
    if data['current_price'] != 'null':
        assert isinstance(data['current_price'], (int, float))
        assert data['current_price'] > 0.0
    
    # Verify volume data
    if data['average_volume'] != 'null':
        assert isinstance(data['average_volume'], (int, float))
        assert data['average_volume'] > 0
    
    # Verify financial metrics lists
    assert isinstance(data['roic'], list), "ROIC should be a list"
    assert isinstance(data['eps'], list), "EPS growth rates should be a list"
    assert isinstance(data['sales'], list), "Sales growth rates should be a list"
    assert isinstance(data['equity'], list), "Equity growth rates should be a list"
    assert isinstance(data['cash'], list), "Free cash flow growth rates should be a list"
    
    # Verify debt metrics
    assert isinstance(data['total_debt'], (int, float))
    assert data['total_debt'] >= 0.0
    
    assert isinstance(data['debt_equity_ratio'], (int, float))
    # Debt-to-equity can be -1 if data unavailable
    assert data['debt_equity_ratio'] >= -1.0
    
    # Verify calculated prices
    assert 'ten_cap_price' in data
    assert 'debt_payoff_time' in data
    assert 'free_cash_flow' in data


def test_yfinance_data_class():
    """
    Test the YFinanceData class directly.
    This replaces the old test_future_growth_rate() test.
    """
    test_ticker = 'MSFT'
    
    # Create YFinanceData instance
    yf_data = YFinanceData(test_ticker)
    
    # Verify initialization
    assert yf_data.ticker_symbol == test_ticker.upper()
    
    # Fetch all data
    success = yf_data.fetch_all_data()
    
    # Verify fetch was successful
    assert success is True, "fetch_all_data() should return True on success"
    
    # Verify company name contains Microsoft
    assert yf_data.name is not None
    assert 'Microsoft' in yf_data.name
    
    # Verify description is populated
    assert yf_data.description != ''
    
    # Verify industry is populated
    assert yf_data.industry != ''
    
    # Verify price data
    if yf_data.current_price:
        assert yf_data.current_price > 0.0
    
    if yf_data.average_volume:
        assert yf_data.average_volume > 0
    
    if yf_data.market_cap:
        assert yf_data.market_cap > 0.0
    
    if yf_data.shares_outstanding:
        assert yf_data.shares_outstanding > 0
    
    # Verify PE ratios (if available)
    if yf_data.pe_high:
        assert yf_data.pe_high > 0.0
    
    if yf_data.pe_low:
        assert yf_data.pe_low > 0.0
    
    # Verify financial metrics are lists (may be empty if data unavailable)
    assert isinstance(yf_data.roic, list)
    assert isinstance(yf_data.roic_averages, list)
    assert isinstance(yf_data.equity, list)
    assert isinstance(yf_data.equity_growth_rates, list)
    assert isinstance(yf_data.free_cash_flow, list)
    assert isinstance(yf_data.free_cash_flow_growth_rates, list)
    assert isinstance(yf_data.revenue, list)
    assert isinstance(yf_data.revenue_growth_rates, list)
    assert isinstance(yf_data.eps, list)
    assert isinstance(yf_data.eps_growth_rates, list)
    
    # Verify debt metrics
    assert yf_data.total_debt >= 0.0
    # Debt-to-equity can be -1 if unavailable
    assert yf_data.debt_equity_ratio >= -1.0


def test_growth_rate_estimation():
    """
    Test that we can get analyst growth rate estimates.
    This is similar to the old test_future_growth_rate() but adapted for yfinance.
    """
    test_ticker = 'MSFT'
    
    # Create YFinanceData instance
    yf_data = YFinanceData(test_ticker)
    
    # Fetch data
    success = yf_data.fetch_all_data()
    assert success is True
    
    # Verify ticker symbol
    assert yf_data.ticker_symbol == test_ticker.upper()
    
    # Check if we got a growth rate estimate
    # Note: This may be None if yfinance doesn't have analyst estimates
    if yf_data.five_year_growth_rate is not None:
        assert isinstance(yf_data.five_year_growth_rate, (int, float))
        # Growth rate should be reasonable (between -100% and 1000%)
        assert -100.0 <= yf_data.five_year_growth_rate <= 1000.0


def test_complete_data_flow():
    """
    Integration test that verifies the complete data flow from yfinance to final output.
    """
    test_ticker = 'AAPL'  # Use Apple for reliable test data
    
    # Fetch complete data
    result = fetchDataForTickerSymbol(test_ticker)
    
    # Verify result structure
    assert result is not None
    assert isinstance(result, dict)
    
    # Verify all expected keys are present
    expected_keys = [
        'ticker', 'name', 'description', 'roic', 'eps', 'sales',
        'equity', 'cash', 'total_debt', 'free_cash_flow',
        'debt_payoff_time', 'debt_equity_ratio', 'current_price',
        'ten_cap_price', 'average_volume', 'margin_of_safety_price',
        'sticker_price', 'payback_time'
    ]
    
    for key in expected_keys:
        assert key in result, f"Expected key '{key}' not found in result"
    
    # Verify ticker matches
    assert result['ticker'] == test_ticker
    
    # Verify name is populated
    assert result['name'] is not None
    assert result['name'] != ''
    assert result['name'] != 'null'


def test_invalid_ticker():
    """
    Test handling of invalid ticker symbols.
    """
    # Test with empty string
    result = fetchDataForTickerSymbol('')
    assert result is None
    
    # Test with None
    result = fetchDataForTickerSymbol(None)
    assert result is None
    
    # Test with invalid ticker (should return None or handle gracefully)
    result = fetchDataForTickerSymbol('INVALIDTICKER12345')
    # May return None or a result with limited data
    # Just verify it doesn't crash


def test_cagr_calculations():
    """
    Test that CAGR calculations work correctly.
    """
    # Test positive growth
    result = YFinanceData._cagr(100, 110, 1)
    assert result is not None
    assert abs(result - 10.0) < 0.1  # Should be ~10%
    
    # Test 5-year growth
    result = YFinanceData._cagr(100, 161.05, 5)
    assert result is not None
    assert abs(result - 10.0) < 0.5  # Should be ~10% CAGR
    
    # Test zero cases
    assert YFinanceData._cagr(0, 100, 5) is None
    assert YFinanceData._cagr(100, 110, 0) is None
    assert YFinanceData._cagr(None, 100, 5) is None


def test_growth_rate_computation():
    """
    Test growth rate computation for different time periods.
    """
    # Test with sufficient data (7+ years)
    data = [100, 110, 121, 133.1, 146.41, 161.05, 177.16, 194.87]
    rates = YFinanceData._compute_growth_rates(data)
    
    # Should return 4 rates: 1yr, 3yr, 5yr, max
    assert len(rates) == 4
    assert all(isinstance(r, (int, float)) for r in rates)
    
    # Test with insufficient data
    data = [100]
    rates = YFinanceData._compute_growth_rates(data)
    assert len(rates) == 0
    
    # Test with None
    rates = YFinanceData._compute_growth_rates(None)
    assert len(rates) == 0


def test_averages_computation():
    """
    Test average computation for different time periods.
    """
    data = [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 24.0]
    averages = YFinanceData._compute_averages(data)
    
    # Should return 4 averages: 1yr, 3yr, 5yr, all-time
    assert len(averages) == 4
    assert averages[0] == 24.0  # Most recent value
    
    # Test with insufficient data
    data = []
    averages = YFinanceData._compute_averages(data)
    assert len(averages) == 0


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
