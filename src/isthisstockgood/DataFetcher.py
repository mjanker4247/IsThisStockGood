# DataFetcher.py - Optimized version using yfinance

import logging
import isthisstockgood.RuleOneInvestingCalculations as RuleOne
from isthisstockgood.YFinanceData import YFinanceData
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

logger = logging.getLogger("IsThisStockGood")

# Cache for frequently requested tickers (reduces API calls)
@lru_cache(maxsize=100)
def fetchDataForTickerSymbol(ticker):
    """
    Fetches and parses all of the financial data for the `ticker`.
    
    OPTIMIZATIONS:
    - Uses yfinance instead of web scraping (faster, more reliable)
    - Single data source reduces network calls
    - Built-in caching via @lru_cache decorator
    - Parallel processing removed (yfinance handles this internally)
    
    Args:
        ticker: The ticker symbol string.
    
    Returns:
        Returns a dictionary of all the processed financial data. If
        there's an error, return None.
        
        Keys include:
        'roic', 'eps', 'sales', 'equity', 'cash', 'long_term_debt',
        'free_cash_flow', 'debt_payoff_time', 'debt_equity_ratio',
        'margin_of_safety_price', 'current_price', 'ten_cap_price'
    """
    if not ticker:
        return None
    
    try:
        # Fetch all data using yfinance
        yf_data = YFinanceData(ticker)
        success = yf_data.fetch_all_data()
        
        if not success:
            logger.error(f"Failed to fetch data for ticker: {ticker}")
            return None
        
        # Get growth rate (using analyst estimate if available, otherwise use historical)
        five_year_growth_rate = yf_data.five_year_growth_rate if yf_data.five_year_growth_rate else 0
        
        # If no analyst estimate, use historical equity growth as fallback
        if five_year_growth_rate == 0 and yf_data.equity_growth_rates:
            five_year_growth_rate = yf_data.equity_growth_rates[-1]
        
        # Calculate margin of safety price
        margin_of_safety_price, sticker_price = _calculateMarginOfSafetyPrice(
            yf_data.equity_growth_rates[-1] if yf_data.equity_growth_rates else None,
            yf_data.pe_low,
            yf_data.pe_high,
            sum(yf_data.quarterly_eps[-4:]) if len(yf_data.quarterly_eps) >= 4 else None,
            five_year_growth_rate
        )
        
        # Calculate payback time
        payback_time = _calculatePaybackTime(
            yf_data.equity_growth_rates[-1] if yf_data.equity_growth_rates else None,
            yf_data.last_year_net_income,
            yf_data.market_cap,
            five_year_growth_rate
        )
        
        # Calculate free cash flow and ten cap price
        free_cash_flow_per_share = float(yf_data.free_cash_flow[-1]) if yf_data.free_cash_flow else 0
        computed_free_cash_flow = round(free_cash_flow_per_share * yf_data.shares_outstanding) if yf_data.shares_outstanding and free_cash_flow_per_share else 0
        ten_cap_price = 10 * free_cash_flow_per_share if free_cash_flow_per_share else 0
        
        # Calculate debt payoff time (avoiding division by zero)
        debt_payoff_time = 0
        if computed_free_cash_flow and computed_free_cash_flow > 0:
            debt_payoff_time = round(float(yf_data.total_debt) / computed_free_cash_flow)
        
        # Build response
        template_values = {
            'ticker': ticker,
            'name': yf_data.name if yf_data.name else 'null',
            'description': yf_data.description if yf_data.description else 'null',
            'roic': yf_data.roic_averages if yf_data.roic_averages else [],
            'eps': yf_data.eps_growth_rates if yf_data.eps_growth_rates else [],
            'sales': yf_data.revenue_growth_rates if yf_data.revenue_growth_rates else [],
            'equity': yf_data.equity_growth_rates if yf_data.equity_growth_rates else [],
            'cash': yf_data.free_cash_flow_growth_rates if yf_data.free_cash_flow_growth_rates else [],
            'total_debt': yf_data.total_debt,
            'free_cash_flow': computed_free_cash_flow,
            'ten_cap_price': round(ten_cap_price, 2),
            'debt_payoff_time': debt_payoff_time,
            'debt_equity_ratio': yf_data.debt_equity_ratio if yf_data.debt_equity_ratio >= 0 else -1,
            'margin_of_safety_price': margin_of_safety_price if margin_of_safety_price else 'null',
            'current_price': yf_data.current_price if yf_data.current_price else 'null',
            'sticker_price': sticker_price if sticker_price else 'null',
            'payback_time': payback_time if payback_time else 'null',
            'average_volume': yf_data.average_volume if yf_data.average_volume else 'null'
        }
        
        return template_values
        
    except Exception as e:
        logger.error(f"Error processing ticker {ticker}: {str(e)}")
        return None


def _calculate_growth_rate_decimal(analyst_growth_rate, current_growth_rate):
    """Convert growth rate percentage to decimal."""
    growth_rate = min(float(analyst_growth_rate), float(current_growth_rate))
    # Divide the growth rate by 100 to convert from percent to decimal.
    return growth_rate / 100.0


def _calculateMarginOfSafetyPrice(one_year_equity_growth_rate, pe_low, pe_high, ttm_eps, analyst_five_year_growth_rate):
    """Calculate margin of safety price and sticker price."""
    if not one_year_equity_growth_rate or not pe_low or not pe_high or not ttm_eps or not analyst_five_year_growth_rate:
        return None, None
    
    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    margin_of_safety_price, sticker_price = \
        RuleOne.margin_of_safety_price(float(ttm_eps), growth_rate, float(pe_low), float(pe_high))
    
    return margin_of_safety_price, sticker_price


def _calculatePaybackTime(one_year_equity_growth_rate, last_year_net_income, market_cap, analyst_five_year_growth_rate):
    """Calculate payback time in years."""
    if not one_year_equity_growth_rate or not last_year_net_income or not market_cap or not analyst_five_year_growth_rate:
        return None
    
    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    payback_time = RuleOne.payback_time(market_cap, last_year_net_income, growth_rate)
    
    return payback_time
