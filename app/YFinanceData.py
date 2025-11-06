# YFinanceData.py - Replaces MSNMoney.py, YahooFinance.py, Zacks.py, and YahooFinanceChart.py

import re
from bs4 import BeautifulSoup
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import pytz

logger = logging.getLogger("IsThisStockGood")

class YFinanceData:
    """
    Consolidated class to fetch all stock data using yfinance library.
    Replaces MSNMoney, YahooFinance, Zacks, and YahooFinanceChart classes.
    
    This provides better performance by:
    - Single library instead of web scraping multiple sources
    - Built-in rate limiting and caching
    - Structured API responses (no HTML parsing)
    - Automatic retry logic
    """
    
    KEY_RATIOS_YEAR_SPAN = 5
    
    def __init__(self, ticker_symbol):
        self.ticker_symbol = ticker_symbol.upper().strip()
        self.ticker = None  # Will hold yf.Ticker object
        
        # Company info
        self.name = ''
        self.description = ''
        self.industry = ''
        
        # Price data
        self.current_price = None
        self.average_volume = None
        self.market_cap = None
        
        # Share data
        self.shares_outstanding = None
        
        # PE Ratios
        self.pe_high = None
        self.pe_low = None
        self.current_pe = None
        
        # Financial metrics arrays
        self.roic = []
        self.roic_averages = []
        self.equity = []
        self.equity_growth_rates = []
        self.free_cash_flow = []
        self.free_cash_flow_growth_rates = []
        self.revenue = []
        self.revenue_growth_rates = []
        self.eps = []
        self.eps_growth_rates = []
        self.quarterly_eps = []
        
        # Debt metrics
        self.debt_equity_ratio = -1
        self.total_debt = 0
        self.last_year_net_income = 0
        
        # Growth estimates
        self.five_year_growth_rate = None
        
    def fetch_all_data(self):
        """
        Fetch all required data in a single call.
        This is more efficient than multiple separate API calls.
        """
        try:
            # Create ticker object (this doesn't make an API call yet)
            self.ticker = yf.Ticker(self.ticker_symbol)
            
            # Fetch all data (yfinance caches responses)
            self._fetch_info()
            self._fetch_financials()
            self._fetch_historical_pe()
            self._fetch_analyst_estimates()
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching data for {self.ticker_symbol}: {str(e)}")
            return False
    
    def fetch_five_year_growth_rate(self):
        """
        Scrapes Zacks website for analyst 5 year growth rate.
        Uses BeautifulSoup for parsing.
        """
        url = f"https://www.zacks.com/stock/quote/{self.ticker_symbol}/detailed-earning-estimates"
        response = requests.get(url)
        if response.status_code != 200 or not response.text:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        lines = soup.get_text("\n").split("\n")
        for i, line in enumerate(lines):
            if "Next 5 Years" in line:
                if i + 1 < len(lines):
                    estimate = lines[i + 1]
                    match = re.search(r"(\d+\.?\d*)", estimate)
                    if match:
                        self.five_year_growth_rate = float(match.group(1))
                        return self.five_year_growth_rate
        return None
    
    def _fetch_info(self):
        """Fetch basic company information and current metrics."""
        try:
            info = self.ticker.info
            
            # Company details
            self.name = info.get('longName', info.get('shortName', ''))
            self.description = info.get('longBusinessSummary', '')
            self.industry = info.get('industry', '')
            
            # Current price and volume
            self.current_price = info.get('currentPrice', info.get('regularMarketPrice', None))
            self.average_volume = info.get('averageVolume', info.get('averageVolume10days', None))
            
            # Market metrics
            self.market_cap = info.get('marketCap', None)
            self.shares_outstanding = info.get('sharesOutstanding', None)
            
            # PE ratio (current/trailing)
            self.current_pe = info.get('trailingPE', info.get('forwardPE', None))
            
        except Exception as e:
            logger.warning(f"Error fetching info for {self.ticker_symbol}: {str(e)}")
    
    def _fetch_financials(self):
        """Fetch and process financial statements."""
        try:
            # Get annual financial statements
            income_stmt = self.ticker.income_stmt  # Most recent year first
            balance_sheet = self.ticker.balance_sheet
            cash_flow = self.ticker.cashflow
            
            # Get quarterly statements for recent EPS
            quarterly_income = self.ticker.quarterly_income_stmt
            
            if income_stmt is None or income_stmt.empty:
                logger.warning(f"No financial data available for {self.ticker_symbol}")
                return
            
            # Extract EPS data (annual)
            self._extract_eps(income_stmt)
            
            # Extract quarterly EPS for TTM calculation
            self._extract_quarterly_eps(quarterly_income)
            
            # Extract equity/book value per share
            self._extract_equity(balance_sheet)
            
            # Extract revenue per share
            self._extract_revenue(income_stmt)
            
            # Extract free cash flow per share
            self._extract_free_cash_flow(cash_flow)
            
            # Calculate ROIC
            self._calculate_roic(income_stmt, balance_sheet)
            
            # Extract debt metrics
            self._extract_debt_metrics(balance_sheet, quarterly_income)
            
        except Exception as e:
            logger.error(f"Error fetching financials for {self.ticker_symbol}: {str(e)}")
    
    def _extract_eps(self, income_stmt):
        """Extract annual EPS data."""
        try:
            # yfinance returns columns in reverse chronological order (newest first)
            # We need to reverse to get oldest first for growth calculations
            if 'Basic EPS' in income_stmt.index:
                eps_data = income_stmt.loc['Basic EPS'].dropna()
                self.eps = eps_data.tolist()[::-1]  # Reverse to oldest first
            elif 'Diluted EPS' in income_stmt.index:
                eps_data = income_stmt.loc['Diluted EPS'].dropna()
                self.eps = eps_data.tolist()[::-1]
            
            # Calculate growth rates
            if self.eps:
                self.eps_growth_rates = self._compute_growth_rates(self.eps)
                
        except Exception as e:
            logger.warning(f"Error extracting EPS: {str(e)}")
    
    def _extract_quarterly_eps(self, quarterly_income):
        """Extract quarterly EPS for TTM calculation."""
        try:
            if quarterly_income is None or quarterly_income.empty:
                return
                
            if 'Basic EPS' in quarterly_income.index:
                quarterly_eps_data = quarterly_income.loc['Basic EPS'].dropna()
                self.quarterly_eps = quarterly_eps_data.tolist()[::-1]  # Reverse to oldest first
            elif 'Diluted EPS' in quarterly_income.index:
                quarterly_eps_data = quarterly_income.loc['Diluted EPS'].dropna()
                self.quarterly_eps = quarterly_eps_data.tolist()[::-1]
            
            # Calculate last year net income from TTM EPS
            if self.quarterly_eps and len(self.quarterly_eps) >= 4 and self.shares_outstanding:
                ttm_eps = sum(self.quarterly_eps[-4:])
                self.last_year_net_income = ttm_eps * self.shares_outstanding
                
        except Exception as e:
            logger.warning(f"Error extracting quarterly EPS: {str(e)}")
    
    def _extract_equity(self, balance_sheet):
        """Extract book value per share (equity)."""
        try:
            if balance_sheet is None or balance_sheet.empty:
                return
            
            # Book value = Total Stockholder Equity / Shares Outstanding
            if 'Stockholders Equity' in balance_sheet.index and self.shares_outstanding:
                equity_data = balance_sheet.loc['Stockholders Equity'].dropna()
                equity_values = (equity_data / self.shares_outstanding).tolist()[::-1]
                self.equity = equity_values
                self.equity_growth_rates = self._compute_growth_rates(self.equity)
            elif 'Total Equity Gross Minority Interest' in balance_sheet.index and self.shares_outstanding:
                equity_data = balance_sheet.loc['Total Equity Gross Minority Interest'].dropna()
                equity_values = (equity_data / self.shares_outstanding).tolist()[::-1]
                self.equity = equity_values
                self.equity_growth_rates = self._compute_growth_rates(self.equity)
                
        except Exception as e:
            logger.warning(f"Error extracting equity: {str(e)}")
    
    def _extract_revenue(self, income_stmt):
        """Extract revenue per share."""
        try:
            if 'Total Revenue' in income_stmt.index and self.shares_outstanding:
                revenue_data = income_stmt.loc['Total Revenue'].dropna()
                revenue_values = (revenue_data / self.shares_outstanding).tolist()[::-1]
                self.revenue = revenue_values
                self.revenue_growth_rates = self._compute_growth_rates(self.revenue)
                
        except Exception as e:
            logger.warning(f"Error extracting revenue: {str(e)}")
    
    def _extract_free_cash_flow(self, cash_flow):
        """Extract free cash flow per share."""
        try:
            if cash_flow is None or cash_flow.empty:
                return
            
            # Free Cash Flow = Operating Cash Flow - Capital Expenditure
            if 'Operating Cash Flow' in cash_flow.index and 'Capital Expenditure' in cash_flow.index:
                operating_cf = cash_flow.loc['Operating Cash Flow'].dropna()
                capex = cash_flow.loc['Capital Expenditure'].dropna()
                
                # Align the data
                common_cols = operating_cf.index.intersection(capex.index)
                if len(common_cols) > 0 and self.shares_outstanding:
                    fcf = (operating_cf[common_cols] + capex[common_cols])  # capex is negative
                    fcf_per_share = (fcf / self.shares_outstanding).tolist()[::-1]
                    self.free_cash_flow = fcf_per_share
                    self.free_cash_flow_growth_rates = self._compute_growth_rates(self.free_cash_flow)
            elif 'Free Cash Flow' in cash_flow.index and self.shares_outstanding:
                # Some tickers have FCF directly
                fcf_data = cash_flow.loc['Free Cash Flow'].dropna()
                fcf_per_share = (fcf_data / self.shares_outstanding).tolist()[::-1]
                self.free_cash_flow = fcf_per_share
                self.free_cash_flow_growth_rates = self._compute_growth_rates(self.free_cash_flow)
                
        except Exception as e:
            logger.warning(f"Error extracting free cash flow: {str(e)}")
    
    def _calculate_roic(self, income_stmt, balance_sheet):
        """Calculate Return on Invested Capital."""
        try:
            if income_stmt is None or balance_sheet is None:
                return
            if income_stmt.empty or balance_sheet.empty:
                return
            
            # ROIC = NOPAT / Invested Capital
            # NOPAT ≈ Operating Income * (1 - Tax Rate) or use Net Income as approximation
            # Invested Capital = Total Assets - Current Liabilities (simplified)
            # Or: Invested Capital = Debt + Equity - Cash
            
            roic_values = []
            
            # Get common time periods
            common_cols = income_stmt.columns.intersection(balance_sheet.columns)
            
            for col in common_cols:
                try:
                    # Get net income
                    net_income = income_stmt.loc['Net Income', col] if 'Net Income' in income_stmt.index else None
                    
                    # Get invested capital components
                    stockholder_equity = None
                    if 'Stockholders Equity' in balance_sheet.index:
                        stockholder_equity = balance_sheet.loc['Stockholders Equity', col]
                    elif 'Total Equity Gross Minority Interest' in balance_sheet.index:
                        stockholder_equity = balance_sheet.loc['Total Equity Gross Minority Interest', col]
                    
                    total_debt = None
                    if 'Total Debt' in balance_sheet.index:
                        total_debt = balance_sheet.loc['Total Debt', col]
                    elif 'Long Term Debt' in balance_sheet.index:
                        total_debt = balance_sheet.loc['Long Term Debt', col]
                    
                    cash = balance_sheet.loc['Cash And Cash Equivalents', col] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
                    
                    if net_income and stockholder_equity and total_debt:
                        invested_capital = stockholder_equity + total_debt - cash
                        if invested_capital > 0:
                            roic = (net_income / invested_capital) * 100
                            roic_values.append(roic)
                except:
                    continue
            
            # Reverse to get oldest first
            self.roic = roic_values[::-1]
            self.roic_averages = self._compute_averages(self.roic)
            
        except Exception as e:
            logger.warning(f"Error calculating ROIC: {str(e)}")
    
    def _extract_debt_metrics(self, balance_sheet, quarterly_income):
        """Extract debt-related metrics."""
        try:
            if balance_sheet is None or balance_sheet.empty:
                return
            
            # Get most recent balance sheet (first column)
            latest_bs = balance_sheet.iloc[:, 0]
            
            # Total debt
            if 'Total Debt' in latest_bs.index:
                self.total_debt = float(latest_bs['Total Debt'])
            elif 'Long Term Debt' in latest_bs.index:
                self.total_debt = float(latest_bs['Long Term Debt'])
            
            # Debt to equity ratio
            stockholder_equity = None
            if 'Stockholders Equity' in latest_bs.index:
                stockholder_equity = latest_bs['Stockholders Equity']
            elif 'Total Equity Gross Minority Interest' in latest_bs.index:
                stockholder_equity = latest_bs['Total Equity Gross Minority Interest']
            
            if self.total_debt and stockholder_equity and stockholder_equity > 0:
                self.debt_equity_ratio = self.total_debt / stockholder_equity
            
        except Exception as e:
            logger.warning(f"Error extracting debt metrics: {str(e)}")
    
    def _fetch_historical_pe(self):
        """Calculate historical PE ratios from price and earnings data."""
        try:
            # Get 5+ years of historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 6)  # 6 years to ensure we have 5 complete years
            
            hist_data = self.ticker.history(start=start_date, end=end_date, interval='1mo')
            
            if hist_data.empty or not self.eps:
                return
            
            # Calculate PE ratios for each month
            pe_ratios = []
            
            # Get annual EPS data with dates
            income_stmt = self.ticker.income_stmt
            if income_stmt is None or income_stmt.empty:
                return
            
            # Build a mapping of date ranges to EPS
            eps_by_date = {}
            if 'Basic EPS' in income_stmt.index:
                eps_series = income_stmt.loc['Basic EPS'].dropna()
                for date, eps_value in eps_series.items():
                    # Convert timezone-aware datetime to timezone-naive for comparison
                    date_naive = date.tz_localize(None) if date.tzinfo else date
                    eps_by_date[date_naive] = eps_value

            # For each month, find the appropriate EPS and calculate PE
            for date, row in hist_data.iterrows():
                price = row['Close']
                # Convert timezone-aware datetime to timezone-naive for comparison
                date_naive = date.tz_localize(None) if hasattr(date, 'tz_localize') and date.tzinfo else date
                
                # Find the most recent EPS before this date
                applicable_eps = None
                for eps_date, eps_val in sorted(eps_by_date.items(), reverse=True):
                    if eps_date <= date_naive:
                        applicable_eps = eps_val
                        break
                
                if applicable_eps and applicable_eps > 0 and price > 0:
                    pe = price / applicable_eps
                    # Filter out unrealistic PE ratios
                    if 0 < pe < 200:  # Reasonable range
                        pe_ratios.append(pe)
            
            # Get 5-year range
            if pe_ratios:
                recent_pe_ratios = pe_ratios[-60:]  # Last 60 months (5 years)
                if len(recent_pe_ratios) >= 12:  # At least 1 year of data
                    self.pe_high = max(recent_pe_ratios)
                    self.pe_low = min(recent_pe_ratios)
            
        except Exception as e:
            logger.warning(f"Error calculating historical PE: {str(e)}")
    
    def _fetch_analyst_estimates(self):
        """Fetch analyst growth rate estimates."""
        try:
            # Get analyst recommendations and estimates
            info = self.ticker.info
            
            # Try to get growth estimate
            # yfinance provides this in the 'info' dict
            growth_estimate = info.get('earningsQuarterlyGrowth', None)
            if not growth_estimate:
                growth_estimate = info.get('earningsGrowth', None)
            
            # Convert to percentage if available
            if growth_estimate:
                self.five_year_growth_rate = growth_estimate * 100
            
            # Alternative: get from recommendations/analysis
            # This is less reliable but can provide additional data
            try:
                analysis = self.ticker.analysis
                if analysis is not None and not analysis.empty:
                    if 'Growth' in analysis.index:
                        growth_data = analysis.loc['Growth'].dropna()
                        if not growth_data.empty:
                            # Get most recent estimate
                            self.five_year_growth_rate = float(growth_data.iloc[0])
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Error fetching analyst estimates: {str(e)}")
    
    @staticmethod
    def _compute_growth_rates(data):
        """
        Compute compound annual growth rates for 1, 3, 5, and max year periods.
        Uses the same logic as original MSNMoney implementation.
        """
        if data is None or len(data) < 2:
            return []
        
        results = []
        
        # 1-year growth rate
        if len(data) >= 2:
            rate = YFinanceData._cagr(data[-2], data[-1], 1)
            if rate is not None:
                results.append(rate)
        
        # 3-year growth rate
        if len(data) >= 4:
            rate = YFinanceData._cagr(data[-4], data[-1], 3)
            if rate is not None:
                results.append(rate)
        
        # 5-year growth rate
        if len(data) >= 6:
            rate = YFinanceData._cagr(data[-6], data[-1], 5)
            if rate is not None:
                results.append(rate)
        
        # Maximum period growth rate
        if len(data) >= 7:
            rate = YFinanceData._cagr(data[0], data[-1], len(data) - 1)
            if rate is not None:
                results.append(rate)
        
        return results
    
    @staticmethod
    def _cagr(start_value, end_value, years):
        """Calculate compound annual growth rate."""
        if start_value is None or end_value is None or years is None:
            return None
        if start_value == 0 or years == 0:
            return None
        
        try:
            if start_value > 0 and end_value > 0:
                # Both positive
                exponent = 1.0 / years
                result = round((pow(end_value / start_value, exponent) - 1.0) * 100, 2)
            elif start_value < 0 and end_value < 0:
                # Both negative
                exponent = 1.0 / years
                result = round((pow(abs(end_value) / abs(start_value), exponent) - 1.0) * 100, 2)
            else:
                # Mixed signs - use approximation
                if start_value < end_value:
                    difference = (end_value - (2.0 * start_value)) / (-1.0 * start_value)
                else:
                    difference = ((-1 * end_value) + start_value) / start_value
                
                exponent = 1.0 / years
                result = round((pow(difference, exponent) - 1.0) * 100, 2)
                if end_value < 0:
                    result = -1 * result
            
            return result
        except:
            return None
    
    @staticmethod
    def _compute_averages(data):
        """Calculate averages for 1, 3, 5, and max year periods."""
        if data is None or len(data) < 1:
            return []
        
        results = []
        
        # 1-year (most recent)
        results.append(round(data[-1], 2))
        
        # 3-year average
        if len(data) >= 3:
            avg = round(sum(data[-3:]) / 3, 2)
            results.append(avg)
        
        # 5-year average
        if len(data) >= 5:
            avg = round(sum(data[-5:]) / 5, 2)
            results.append(avg)
        
        # All-time average
        if len(data) >= 6:
            avg = round(sum(data) / len(data), 2)
            results.append(avg)
        
        return results
