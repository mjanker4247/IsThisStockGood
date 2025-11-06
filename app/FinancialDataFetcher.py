import requests
import yfinance as yf
import re
from bs4 import BeautifulSoup  # Changed from lxml to BeautifulSoup


class FinancialDataFetcher:
    """
    Consolidated financial data fetcher class.
    Uses yfinance for most data and web scraping for analyst growth rates.
    """

    def __init__(self, ticker_symbol):
        self.ticker_symbol = ticker_symbol.upper()
        self.yf_ticker = yf.Ticker(self.ticker_symbol)
        self.five_year_growth_rate = None

    def fetch_summary_data(self):
        """
        Fetches general summary data such as price, market cap, 
        shares outstanding, P/E ratios, etc. from yfinance.
        """
        info = self.yf_ticker.info
        data = {}
        data['current_price'] = info.get('currentPrice')
        data['market_cap'] = info.get('marketCap')
        data['shares_outstanding'] = info.get('sharesOutstanding')
        data['pe_ratio'] = info.get('trailingPE')
        data['forward_pe_ratio'] = info.get('forwardPE')
        data['eps'] = info.get('trailingEps')
        data['revenue'] = info.get('totalRevenue')
        data['free_cash_flow'] = info.get('freeCashflow')
        data['debt_to_equity'] = info.get('debtToEquity')
        data['return_on_equity'] = info.get('returnOnEquity')
        return data

    def fetch_financials(self):
        """
        Fetches financial statements data such as yearly earnings,
        revenue, cash flows from yfinance financials and cashflow.
        Useful for growth calculation externally if needed.
        """
        financials = self.yf_ticker.financials
        cashflow = self.yf_ticker.cashflow
        earnings = self.yf_ticker.earnings
        return {
            'financials': financials,
            'cashflow': cashflow,
            'earnings': earnings
        }

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

    def fetch_all(self):
        """
        Convenience method to fetch all relevant data
        """
        data = self.fetch_summary_data()
        data['five_year_growth_rate'] = self.fetch_five_year_growth_rate()
        return data
