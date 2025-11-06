from app.CompanyInfo import CompanyInfo
from app.FinancialDataFetcher import FinancialDataFetcher
import logging

logger = logging.getLogger("IsThisStockGood")

def fetchDataForTickerSymbol(ticker):
    """
    Fetch and consolidate financial data for a ticker using FinancialDataFetcher.
    Returns a CompanyInfo object or None on error.
    """
    if not ticker:
        logger.warning("Empty ticker symbol provided.")
        return None

    try:
        fetcher = FinancialDataFetcher(ticker)
        # Fetch consolidated data
        data = fetcher.fetch_all()
        if not data:
            logger.error(f"Failed to fetch data for ticker {ticker}")
            return None

        # Populate CompanyInfo dataclass
        company_info = CompanyInfo(
            tickersymbol=ticker,
            name=None,  # Can be added if fetcher extended to provide name
            description=None,
            industry=None,
            currentprice=data.get('current_price', 0.0),
            averagevolume=0,  # Can be added similarly
            marketcap=data.get('market_cap', 0),
            sharesoutstanding=data.get('shares_outstanding', 0),
            pehigh=data.get('pe_ratio', 0.0),
            pelow=data.get('forward_pe_ratio', 0.0),
            roic=data.get('return_on_equity', 0.0),
            roicaverages=[],
            equity=0.0,
            equitygrowthrates=[],
            freecashflow=data.get('free_cash_flow', 0),
            freecashflowgrowthrates=[],
            revenue=data.get('revenue', 0),
            revenuegrowthrates=[],
            eps=data.get('eps', 0.0),
            quarterlyeps=[],
            epsgrowthrates=[],
            debtequityratio=data.get('debt_to_equity', 0.0),
            lastyearnetincome=0.0,
            totaldebt=0.0
        )
        return company_info

    except Exception as e:
        logger.error(f"Exception fetching ticker {ticker}: {e}")
        return None
