# test_yfinance_data.py - COMPLETE FIX with Mock Isolation

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from isthisstockgood.YFinanceData import YFinanceData
from isthisstockgood.DataFetcher import fetchDataForTickerSymbol


class TestYFinanceData(unittest.TestCase):
    """Test suite for YFinanceData class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_ticker = "AAPL"
        self.yf_data = YFinanceData(self.test_ticker)

    def test_initialization(self):
        """Test proper initialization of YFinanceData object"""
        self.assertEqual(self.yf_data.ticker_symbol, "AAPL")
        self.assertIsNone(self.yf_data.ticker)
        self.assertEqual(self.yf_data.name, '')
        self.assertEqual(self.yf_data.roic, [])
        self.assertEqual(self.yf_data.eps, [])
        self.assertIsNone(self.yf_data.current_price)
        self.assertEqual(self.yf_data.debt_equity_ratio, -1)

    def test_ticker_symbol_normalization(self):
        """Test that ticker symbols are properly normalized"""
        test_cases = [
            ("aapl", "AAPL"),
            ("  tsla  ", "TSLA"),
            ("msft", "MSFT"),
        ]
        for input_ticker, expected in test_cases:
            yf_data = YFinanceData(input_ticker)
            self.assertEqual(yf_data.ticker_symbol, expected)

    def test_cagr_calculation_positive_values(self):
        """Test CAGR calculation with positive values"""
        # 10% annual growth
        result = YFinanceData._cagr(100, 110, 1)
        self.assertAlmostEqual(result, 10.0, places=2)

        # 5 year growth from 100 to 161.05 (~10% CAGR)
        result = YFinanceData._cagr(100, 161.05, 5)
        self.assertAlmostEqual(result, 10.0, places=1)

    def test_cagr_calculation_negative_values(self):
        """Test CAGR calculation with negative values"""
        # Both negative
        result = YFinanceData._cagr(-100, -110, 1)
        self.assertAlmostEqual(result, 10.0, places=2)

    def test_cagr_calculation_edge_cases(self):
        """Test CAGR calculation edge cases"""
        # Zero start value
        result = YFinanceData._cagr(0, 100, 5)
        self.assertIsNone(result)

        # Zero years
        result = YFinanceData._cagr(100, 110, 0)
        self.assertIsNone(result)

        # None values
        result = YFinanceData._cagr(None, 100, 5)
        self.assertIsNone(result)

    def test_compute_growth_rates(self):
        """Test growth rate computation for different data lengths"""
        # Test with 8 data points (should return 4 rates)
        data = [100, 110, 121, 133.1, 146.41, 161.05, 177.16, 194.87]
        rates = YFinanceData._compute_growth_rates(data)
        self.assertEqual(len(rates), 4)

        # Test with 6 data points (should return 3 rates)
        data = [100, 110, 121, 133.1, 146.41, 161.05]
        rates = YFinanceData._compute_growth_rates(data)
        self.assertEqual(len(rates), 3)

        # Test with insufficient data
        data = [100]
        rates = YFinanceData._compute_growth_rates(data)
        self.assertEqual(len(rates), 0)

    def test_compute_averages(self):
        """Test average computation for different data lengths"""
        # Test with 6+ years of data
        data = [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 24.0]
        averages = YFinanceData._compute_averages(data)
        self.assertEqual(len(averages), 4)
        self.assertEqual(averages[0], 24.0)

        # Test with insufficient data
        data = []
        averages = YFinanceData._compute_averages(data)
        self.assertEqual(len(averages), 0)

    @patch('yfinance.Ticker')
    def test_fetch_info_success(self, mock_ticker_class):
        """Test successful fetching of company info"""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'longBusinessSummary': 'Technology company',
            'industry': 'Consumer Electronics',
            'currentPrice': 150.0,
            'averageVolume': 50000000,
            'marketCap': 2500000000000,
            'sharesOutstanding': 16000000000,
            'trailingPE': 25.5
        }
        mock_ticker_class.return_value = mock_ticker

        yf_data = YFinanceData("AAPL")
        yf_data.ticker = mock_ticker
        yf_data._fetch_info()

        self.assertEqual(yf_data.name, 'Apple Inc.')
        self.assertEqual(yf_data.description, 'Technology company')
        self.assertEqual(yf_data.industry, 'Consumer Electronics')
        self.assertEqual(yf_data.current_price, 150.0)
        self.assertEqual(yf_data.average_volume, 50000000)
        self.assertEqual(yf_data.market_cap, 2500000000000)
        self.assertEqual(yf_data.shares_outstanding, 16000000000)
        self.assertEqual(yf_data.current_pe, 25.5)

    @patch('yfinance.Ticker')
    def test_extract_eps(self, mock_ticker_class):
        """Test EPS extraction from income statement"""
        dates = pd.date_range('2019-12-31', periods=5, freq='YE')
        eps_values_newest_first = [7.0, 6.5, 6.0, 5.5, 5.0]
        
        # Create proper DataFrame structure
        data_dict = {}
        for i, date in enumerate(dates[::-1]):
            data_dict[date] = {'Basic EPS': eps_values_newest_first[i]}
        
        mock_income_stmt = pd.DataFrame(data_dict).T.T

        mock_ticker = MagicMock()
        mock_ticker.income_stmt = mock_income_stmt

        yf_data = YFinanceData("TEST")
        yf_data.ticker = mock_ticker
        yf_data._extract_eps(mock_income_stmt)

        expected_eps_oldest_first = [5.0, 5.5, 6.0, 6.5, 7.0]
        self.assertEqual(yf_data.eps, expected_eps_oldest_first)
        self.assertIsInstance(yf_data.eps_growth_rates, list)
        self.assertGreater(len(yf_data.eps_growth_rates), 0)

    @patch('yfinance.Ticker')
    def test_extract_debt_metrics(self, mock_ticker_class):
        """Test debt metrics extraction"""
        mock_balance_sheet = pd.DataFrame({
            '2023-12-31': {
                'Total Debt': 100000000000,
                'Stockholders Equity': 50000000000,
            }
        })

        yf_data = YFinanceData("TEST")
        yf_data._extract_debt_metrics(mock_balance_sheet, None)

        self.assertEqual(yf_data.total_debt, 100000000000)
        self.assertEqual(yf_data.debt_equity_ratio, 2.0)


class TestDataFetcher(unittest.TestCase):
    """Test suite for DataFetcher module"""

    @patch('isthisstockgood.DataFetcher.YFinanceData')
    def test_fetch_data_for_ticker_symbol_success(self, mock_yf_data_class):
        """Test successful data fetching and processing"""
        # CRITICAL: Reset mock to prevent interference
        mock_yf_data_class.reset_mock()
        
        # Create FRESH mock instance
        mock_yf_instance = MagicMock()
        mock_yf_data_class.return_value = mock_yf_instance
        
        mock_yf_instance.fetch_all_data.return_value = True
        mock_yf_instance.name = "Apple Inc."
        mock_yf_instance.description = "Technology company"
        mock_yf_instance.current_price = 150.0
        mock_yf_instance.average_volume = 50000000
        mock_yf_instance.market_cap = 2500000000000
        mock_yf_instance.shares_outstanding = 16000000000
        mock_yf_instance.roic_averages = [15.0, 14.5, 14.0]
        mock_yf_instance.eps_growth_rates = [10.0, 9.5, 9.0]
        mock_yf_instance.revenue_growth_rates = [8.0, 7.5, 7.0]
        mock_yf_instance.equity_growth_rates = [12.0, 11.5, 11.0]
        mock_yf_instance.free_cash_flow_growth_rates = [15.0, 14.0, 13.0]
        mock_yf_instance.free_cash_flow = [5.0, 5.5, 6.0, 6.5]
        mock_yf_instance.quarterly_eps = [1.5, 1.6, 1.7, 1.8]
        mock_yf_instance.pe_high = 30.0
        mock_yf_instance.pe_low = 15.0
        mock_yf_instance.total_debt = 100000000000
        mock_yf_instance.debt_equity_ratio = 1.5
        mock_yf_instance.last_year_net_income = 100000000000
        mock_yf_instance.five_year_growth_rate = 10.0

        result = fetchDataForTickerSymbol("AAPL")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        
        required_keys = [
            'ticker', 'name', 'description', 'roic', 'eps', 'sales',
            'equity', 'cash', 'total_debt', 'free_cash_flow',
            'debt_payoff_time', 'debt_equity_ratio', 'current_price',
            'ten_cap_price', 'average_volume'
        ]
        for key in required_keys:
            self.assertIn(key, result)

        self.assertIsInstance(result['ticker'], str)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['roic'], list)
        self.assertIsInstance(result['eps'], list)
        self.assertIsInstance(result['total_debt'], (int, float))
        self.assertIsInstance(result['debt_equity_ratio'], (int, float))

    def test_fetch_data_invalid_ticker(self):
        """Test handling of invalid ticker symbol"""
        result = fetchDataForTickerSymbol("")
        self.assertIsNone(result)

        result = fetchDataForTickerSymbol(None)
        self.assertIsNone(result)

    @patch('isthisstockgood.DataFetcher.YFinanceData')
    def test_fetch_data_api_failure(self, mock_yf_data_class):
        """Test handling of API failure"""
        # CRITICAL: Reset mock to prevent interference
        mock_yf_data_class.reset_mock()
        
        mock_yf_instance = MagicMock()
        mock_yf_instance.fetch_all_data.return_value = False
        mock_yf_data_class.return_value = mock_yf_instance

        result = fetchDataForTickerSymbol("INVALID")
        self.assertIsNone(result)

    @patch('isthisstockgood.DataFetcher.YFinanceData')
    def test_ten_cap_price_calculation(self, mock_yf_data_class):
        """
        Test ten cap price calculation with proper mock isolation.
        
        FIXED: Added explicit mock reset to prevent test interference.
        """
        # CRITICAL: Reset mock to prevent interference from other tests
        mock_yf_data_class.reset_mock()
        
        # Create FRESH mock instance
        mock_yf_instance = MagicMock()
        mock_yf_data_class.return_value = mock_yf_instance
        
        # Set up fresh test data
        mock_yf_instance.fetch_all_data.return_value = True
        mock_yf_instance.free_cash_flow = [5.0, 6.0, 7.0, 8.0, 10.0]  # Latest is 10.0
        mock_yf_instance.shares_outstanding = 1000000
        mock_yf_instance.name = "Test Company"
        mock_yf_instance.description = "Test"
        mock_yf_instance.roic_averages = [15.0]
        mock_yf_instance.eps_growth_rates = [10.0]
        mock_yf_instance.revenue_growth_rates = [8.0]
        mock_yf_instance.equity_growth_rates = [12.0]
        mock_yf_instance.free_cash_flow_growth_rates = [15.0]
        mock_yf_instance.total_debt = 0
        mock_yf_instance.debt_equity_ratio = 0
        mock_yf_instance.current_price = 150.0
        mock_yf_instance.average_volume = 1000000
        mock_yf_instance.quarterly_eps = [1.0, 1.0, 1.0, 1.0]
        mock_yf_instance.pe_high = 30.0
        mock_yf_instance.pe_low = 15.0
        mock_yf_instance.five_year_growth_rate = 10.0
        mock_yf_instance.last_year_net_income = 1000000
        mock_yf_instance.market_cap = 150000000

        result = fetchDataForTickerSymbol("TEST")

        # Ten cap price = 10 × FCF[-1] = 10 × 10.0 = 100.0
        self.assertEqual(result['ten_cap_price'], 100.0,
            "Ten cap price should be 10 × $10 FCF per share (latest value) = $100")

    @patch('isthisstockgood.DataFetcher.YFinanceData')
    def test_debt_payoff_time_calculation(self, mock_yf_data_class):
        """Test debt payoff time calculation"""
        # CRITICAL: Reset mock to prevent interference
        mock_yf_data_class.reset_mock()
        
        mock_yf_instance = MagicMock()
        mock_yf_data_class.return_value = mock_yf_instance
        
        mock_yf_instance.fetch_all_data.return_value = True
        mock_yf_instance.free_cash_flow = [3.0, 4.0, 5.0]
        mock_yf_instance.shares_outstanding = 1000000
        mock_yf_instance.total_debt = 10000000
        mock_yf_instance.name = "Test Company"
        mock_yf_instance.description = "Test"
        mock_yf_instance.roic_averages = [15.0]
        mock_yf_instance.eps_growth_rates = [10.0]
        mock_yf_instance.revenue_growth_rates = [8.0]
        mock_yf_instance.equity_growth_rates = [12.0]
        mock_yf_instance.free_cash_flow_growth_rates = [15.0]
        mock_yf_instance.debt_equity_ratio = 1.0
        mock_yf_instance.current_price = 150.0
        mock_yf_instance.average_volume = 1000000
        mock_yf_instance.quarterly_eps = [1.0, 1.0, 1.0, 1.0]
        mock_yf_instance.pe_high = 30.0
        mock_yf_instance.pe_low = 15.0
        mock_yf_instance.five_year_growth_rate = 10.0
        mock_yf_instance.last_year_net_income = 1000000
        mock_yf_instance.market_cap = 150000000

        result = fetchDataForTickerSymbol("TEST")

        self.assertEqual(result['debt_payoff_time'], 2)


class TestIntegration(unittest.TestCase):
    """Integration tests with real API calls (optional - can be slow)"""

    @unittest.skip("Skip by default to avoid API rate limits")
    def test_real_api_call_aapl(self):
        """Test real API call with Apple stock"""
        result = fetchDataForTickerSymbol("AAPL")

        self.assertIsNotNone(result)
        self.assertEqual(result['ticker'], 'AAPL')
        self.assertIsInstance(result['name'], str)
        self.assertGreater(len(result['name']), 0)

        if result['current_price'] != 'null':
            self.assertIsInstance(result['current_price'], (int, float))
            self.assertGreater(result['current_price'], 0)

    @unittest.skip("Skip by default to avoid API rate limits")
    def test_real_api_call_msft(self):
        """Test real API call with Microsoft stock"""
        result = fetchDataForTickerSymbol("MSFT")

        self.assertIsNotNone(result)
        self.assertEqual(result['ticker'], 'MSFT')
        self.assertIsInstance(result['roic'], list)
        self.assertIsInstance(result['eps'], list)


def run_tests():
    """Run all tests and generate report"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestYFinanceData))
    suite.addTests(loader.loadTestsFromTestCase(TestDataFetcher))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)

    return result


if __name__ == '__main__':
    run_tests()
