import logging
import yfinance as yf
from requests_cache import CachedSession
import pandas as pd
from typing import Optional, Dict, Any
import isthisstockgood.RuleOneInvestingCalculations as RuleOne

logger = logging.getLogger("IsThisStockGood")
# Cache configuration
CACHE_EXPIRE_SECONDS = 300  # 5 minutes

# Create in-memory cache session (no database needed!)
def create_cached_session():
  """Create a requests session with in-memory caching."""
  try:
      # Use memory backend - no files, no database, just RAM
      session = CachedSession(
          cache_name='yfinance_cache',
          backend='memory',  # In-memory only
          expire_after=CACHE_EXPIRE_SECONDS,
          allowable_codes=[200, 404],
          allowable_methods=['GET', 'POST'],
          match_headers=False,
          stale_if_error=True,
      )
      
      logger.info("In-memory cache session created successfully")
      return session
      
  except Exception as e:
      logger.error(f"Error creating cached session: {e}")
      return None

# Create global cached session (reused across requests)
_cached_session = create_cached_session()

def fetchDataForTickerSymbol(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetches financial data using yfinance library.
    
    This replaces ALL custom scrapers (MSNMoney, YahooFinance, Zacks)
    with a single, maintained library.
    """
    if not ticker:
        return None
    
    ticker = ticker.strip().upper()
    
    try:
        # Use cached session if available, otherwise direct yfinance
        if _cached_session:
            stock = yf.Ticker(ticker, session=_cached_session)
        else:
            stock = yf.Ticker(ticker)
        
        # Get all data at once (much faster than multiple requests)
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # Validate we got data
        if not info or 'currentPrice' not in info:
            logger.warning(f"No data available for {ticker}")
            return None
        
        # Extract data using simple dictionary lookups
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        market_cap = info.get('marketCap', 0)
        shares_outstanding = info.get('sharesOutstanding', 0)
        
        # Financial metrics
        pe_high = info.get('fiftyTwoWeekHigh', 0) / info.get('trailingEps', 1) if info.get('trailingEps') else 0
        pe_low = info.get('fiftyTwoWeekLow', 0) / info.get('trailingEps', 1) if info.get('trailingEps') else 0
        
        # Growth rates from financials
        equity_growth_rates = calculate_growth_rates(balance_sheet, 'Total Stockholder Equity')
        eps_growth_rates = calculate_growth_rates_from_info(info, 'earningsQuarterlyGrowth')
        revenue_growth_rates = calculate_growth_rates(financials, 'Total Revenue')
        fcf_growth_rates = calculate_growth_rates(cash_flow, 'Free Cash Flow')
        
        # Get analyst growth estimate (replaces Yahoo/Zacks scraping)
        analyst_growth_rate = info.get('earningsGrowth', 0) * 100  # Convert to percentage
        
        # ROIC calculation
        roic = calculate_roic(info, balance_sheet)
        
        # Debt metrics
        total_debt = info.get('totalDebt', 0)
        total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in balance_sheet.index else 0
        debt_equity_ratio = total_debt / total_equity if total_equity else -1
        
        # Free cash flow
        free_cash_flow = cash_flow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cash_flow.index else 0
        free_cash_flow_per_share = free_cash_flow / shares_outstanding if shares_outstanding else 0
        
        # EPS data
        ttm_eps = info.get('trailingEps', 0)
        quarterly_eps = get_quarterly_eps(stock)
        
        # Calculate Rule #1 metrics
        margin_of_safety_price, sticker_price = _calculateMarginOfSafetyPrice(
            equity_growth_rates[-1] if equity_growth_rates else 0,
            pe_low,
            pe_high,
            ttm_eps,
            analyst_growth_rate
        )
        
        payback_time = _calculatePaybackTime(
            equity_growth_rates[-1] if equity_growth_rates else 0,
            info.get('netIncomeToCommon', 0),
            market_cap,
            analyst_growth_rate
        )
        
        ten_cap_price = 10 * free_cash_flow_per_share
        
        # Build response
        template_values = {
            'ticker': ticker,
            'name': info.get('longName', 'N/A'),
            'description': info.get('longBusinessSummary', 'N/A'),
            'roic': [roic] if roic else [],
            'eps': eps_growth_rates,
            'sales': revenue_growth_rates,
            'equity': equity_growth_rates,
            'cash': fcf_growth_rates,
            'total_debt': total_debt,
            'free_cash_flow': round(free_cash_flow),
            'ten_cap_price': round(ten_cap_price, 2),
            'debt_payoff_time': round(total_debt / free_cash_flow) if free_cash_flow else 'N/A',
            'debt_equity_ratio': debt_equity_ratio,
            'margin_of_safety_price': margin_of_safety_price if margin_of_safety_price else 'null',
            'current_price': current_price,
            'sticker_price': sticker_price if sticker_price else 'null',
            'payback_time': payback_time if payback_time else 'null',
            'average_volume': info.get('averageVolume', 'null')
        }
        
        return template_values
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}", exc_info=True)
        return None


def calculate_growth_rates(df: pd.DataFrame, metric: str, years: int = 5) -> list:
    """Calculate year-over-year growth rates from financial DataFrame."""
    if metric not in df.index:
        return []
    
    values = df.loc[metric].dropna().sort_index()
    if len(values) < 2:
        return []
    
    growth_rates = []
    for i in range(1, min(len(values), years + 1)):
        if values.iloc[i-1] != 0:
            growth_rate = ((values.iloc[i] - values.iloc[i-1]) / abs(values.iloc[i-1])) * 100
            growth_rates.append(round(growth_rate, 2))
    
    return growth_rates


def calculate_growth_rates_from_info(info: dict, key: str) -> list:
    """Extract growth rate from info dict."""
    value = info.get(key, 0)
    if value:
        return [round(value * 100, 2)]
    return []


def calculate_roic(info: dict, balance_sheet: pd.DataFrame) -> float:
    """Calculate Return on Invested Capital."""
    try:
        net_income = info.get('netIncomeToCommon', 0)
        total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in balance_sheet.index else 0
        total_debt = info.get('totalDebt', 0)
        
        invested_capital = total_equity + total_debt
        if invested_capital:
            roic = (net_income / invested_capital) * 100
            return round(roic, 2)
    except Exception as e:
        logger.warning(f"Error calculating ROIC: {e}")
    
    return 0


def get_quarterly_eps(stock: yf.Ticker) -> list:
    """Get last 4 quarters of EPS."""
    try:
        earnings = stock.quarterly_earnings
        if earnings is not None and not earnings.empty:
            eps_values = earnings['Earnings'].tail(4).tolist()
            return [round(val, 2) for val in eps_values]
    except Exception as e:
        logger.warning(f"Error fetching quarterly EPS: {e}")
    
    return []


def _calculate_growth_rate_decimal(analyst_growth_rate: float, current_growth_rate: float) -> float:
    """Convert growth rate from percentage to decimal."""
    growth_rate = min(float(analyst_growth_rate), float(current_growth_rate))
    return growth_rate / 100.0


def _calculateMarginOfSafetyPrice(one_year_equity_growth_rate, pe_low, pe_high, ttm_eps, analyst_five_year_growth_rate):
    """Calculate margin of safety and sticker price using Rule #1."""
    if not all([one_year_equity_growth_rate, pe_low, pe_high, ttm_eps, analyst_five_year_growth_rate]):
        return None, None
    
    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    margin_of_safety_price, sticker_price = \
        RuleOne.margin_of_safety_price(float(ttm_eps), growth_rate, float(pe_low), float(pe_high))
    
    return margin_of_safety_price, sticker_price


def _calculatePaybackTime(one_year_equity_growth_rate, last_year_net_income, market_cap, analyst_five_year_growth_rate):
    """Calculate payback time using Rule #1."""
    if not all([one_year_equity_growth_rate, last_year_net_income, market_cap, analyst_five_year_growth_rate]):
        return None
    
    growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
    payback_time = RuleOne.payback_time(market_cap, last_year_net_income, growth_rate)
    
    return payback_time

# Optional: Function to clear cache manually
def clear_cache():
    """Clear the in-memory cache."""
    global _cached_session
    if _cached_session:
        _cached_session.cache.clear()
        logger.info("Cache cleared")


# Optional: Function to get cache stats
def get_cache_stats():
    """Get cache statistics."""
    if _cached_session and hasattr(_cached_session.cache, 'responses'):
        return {
            'size': len(_cached_session.cache.responses),
            'keys': list(_cached_session.cache.responses.keys())[:10]  # First 10 keys
        }
    return {'size': 0}