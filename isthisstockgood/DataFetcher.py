import random
import logging
import isthisstockgood.RuleOneInvestingCalculations as RuleOne
from requests_futures.sessions import FuturesSession
from isthisstockgood.Active.MSNMoney import MSNMoney
from isthisstockgood.Active.YahooFinance import YahooFinanceAnalysis
from isthisstockgood.Active.Zacks import Zacks
from threading import Lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import wait, FIRST_EXCEPTION

logger = logging.getLogger("IsThisStockGood")

# Request timeout configuration (connect, read)
DEFAULT_TIMEOUT = (3, 10)

def fetchDataForTickerSymbol(ticker):
  """Fetches and parses all of the financial data for the `ticker`.

    Args:
      ticker: The ticker symbol string.

    Returns:
      Returns a dictionary of all the processed financial data. If
      there's an error, return None.

      Keys include:
        'roic',
        'eps',
        'sales',
        'equity',
        'cash',
        'long_term_debt',
        'free_cash_flow',
        'debt_payoff_time',
        'debt_equity_ratio',
        'margin_of_safety_price',
        'current_price'
        'ten_cap_price'
  """
  if not ticker:
    return None
  
  # Normalize ticker early
  ticker = ticker.strip().upper()

  data_fetcher = DataFetcher(ticker)

  # Make all network request asynchronously to build their portion of
  # the json results.
  data_fetcher.fetch_msn_money_data()
  data_fetcher.fetch_yahoo_finance_analysis()
  data_fetcher.fetch_zacks_analysis()


  # Wait for all to complete with timeout
  completed, pending = wait(
      data_fetcher.rpcs, 
      timeout=15,  # 15 second timeout
      return_when=FIRST_EXCEPTION
  )
  
  # Cancel pending requests if timeout
  for future in pending:
      future.cancel()
      logger.warning(f"Request timeout for {ticker}, cancelled pending request")
  
  # Early exit if critical data missing
  if not data_fetcher.msn_money:
      logger.warning(f"Failed to fetch MSN Money data for {ticker}")
      return None

  msn_money = data_fetcher.msn_money
  yahoo_finance_analysis = data_fetcher.yahoo_finance_analysis
  zacks_analysis = data_fetcher.zacks_analysis
  # NOTE: Some stocks won't have analyst growth rates, such as newly listed stocks or some foreign stocks.
  five_year_growth_rate = \
      yahoo_finance_analysis.five_year_growth_rate if yahoo_finance_analysis \
      else zacks_analysis.five_year_growth_rate if zacks_analysis \
      else 0
  margin_of_safety_price, sticker_price = _calculateMarginOfSafetyPrice(
          msn_money.equity_growth_rates[-1],
          msn_money.pe_low,
          msn_money.pe_high,
          sum(msn_money.quarterly_eps[-4:]),
          five_year_growth_rate
      )
  payback_time = _calculatePaybackTime(msn_money.equity_growth_rates[-1], msn_money.last_year_net_income, msn_money.market_cap, five_year_growth_rate)
  free_cash_flow_per_share = float(msn_money.free_cash_flow[-1])
  computed_free_cash_flow = round(free_cash_flow_per_share * msn_money.shares_outstanding)
  ten_cap_price = 10 * free_cash_flow_per_share
  template_values = {
    'ticker' : ticker,
    'name' : msn_money.name if msn_money and msn_money.name else 'null',
    'description': msn_money.description if msn_money and msn_money.description else 'null',
    'roic': msn_money.roic_averages if msn_money and msn_money.roic_averages else [],
    'eps': msn_money.eps_growth_rates if msn_money and msn_money.eps_growth_rates else [],
    'sales': msn_money.revenue_growth_rates if msn_money and msn_money.revenue_growth_rates else [],
    'equity': msn_money.equity_growth_rates if msn_money and msn_money.equity_growth_rates else [],
    'cash': msn_money.free_cash_flow_growth_rates if msn_money and msn_money.free_cash_flow_growth_rates else [],
    'total_debt' : msn_money.total_debt,
    'free_cash_flow' : computed_free_cash_flow,
    'ten_cap_price' : round(ten_cap_price, 2),
    'debt_payoff_time' : round(float(msn_money.total_debt) / computed_free_cash_flow),
    'debt_equity_ratio' : msn_money.debt_equity_ratio if msn_money and msn_money.debt_equity_ratio >= 0 else -1,
    'margin_of_safety_price' : margin_of_safety_price if margin_of_safety_price else 'null',
    'current_price' : msn_money.current_price if msn_money and msn_money.current_price else 'null',
    'sticker_price' : sticker_price if sticker_price else 'null',
    'payback_time' : payback_time if payback_time else 'null',
    'average_volume' : msn_money.average_volume if msn_money and msn_money.average_volume else 'null'
  }
  return template_values


def _calculate_growth_rate_decimal(analyst_growth_rate, current_growth_rate):
  growth_rate = min(float(analyst_growth_rate), float(current_growth_rate))
  # Divide the growth rate by 100 to convert from percent to decimal.
  return growth_rate / 100.0


def _calculateMarginOfSafetyPrice(one_year_equity_growth_rate, pe_low, pe_high, ttm_eps, analyst_five_year_growth_rate):
  if not one_year_equity_growth_rate or not pe_low or not pe_high or not ttm_eps or not analyst_five_year_growth_rate:
    return None, None

  growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
  margin_of_safety_price, sticker_price = \
      RuleOne.margin_of_safety_price(float(ttm_eps), growth_rate, float(pe_low), float(pe_high))
  return margin_of_safety_price, sticker_price


def _calculatePaybackTime(one_year_equity_growth_rate, last_year_net_income, market_cap, analyst_five_year_growth_rate):
  if not one_year_equity_growth_rate or not last_year_net_income or not market_cap or not analyst_five_year_growth_rate:
    return None

  growth_rate = _calculate_growth_rate_decimal(analyst_five_year_growth_rate, one_year_equity_growth_rate)
  payback_time = RuleOne.payback_time(market_cap, last_year_net_income, growth_rate)
  return payback_time


class DataFetcher():
  """A helper class that syncronizes all of the async data fetches."""

  # Class-level session pool for reuse
  _session_pool = None
  _session_lock = Lock()

  USER_AGENT_LIST = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
  ]

  def __init__(self, ticker):
    self.lock = Lock()
    self.rpcs = []
    self.ticker_symbol = ticker
    self.msn_money = None
    self.yahoo_finance_analysis = None
    self.zacks_analysis = None
    self.yahoo_finance_chart = None
    self.error = False

    # Initialize session pool if needed
    if DataFetcher._session_pool is None:
        with DataFetcher._session_lock:
            if DataFetcher._session_pool is None:
                DataFetcher._session_pool = self._create_persistent_session()

  def _create_persistent_session(self):
    """Create a persistent session with connection pooling and retries."""
    session = FuturesSession(max_workers=10)

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': random.choice(DataFetcher.USER_AGENT_LIST)
    })

    return session
  
  def _create_session(self):
    """Return the pooled session."""
    return DataFetcher._session_pool

  def fetch_msn_money_data(self):
    """
    Fetching PE Ratios to calculate Sticker Price and Safety Margin Price. As well as
    the "Big 5" growth rate numbers.
    First we need to get an internal MSN stock id for a ticker and then fetch the data.
    """
    self.msn_money = MSNMoney(self.ticker_symbol)
    session = self._create_session()
    rpc = session.get(self.msn_money.get_ticker_autocomplete_url(), 
                      allow_redirects=True, 
                      timeout=DEFAULT_TIMEOUT,
                      hooks={
                        'response': self.continue_fetching_msn_money_data,
                      })
    self.rpcs.append(rpc)

  def continue_fetching_msn_money_data(self, response, *args, **kwargs):
    """
    After msn_stock_id was fetched in fetch_msn_money_data method
    we can now get the financials.
    """
    try:
      if response.status_code != 200:
        logger.warning(f"MSN autocomplete failed: {response.status_code}")
        return

      msn_stock_id = self.msn_money.extract_stock_id(response.text)
      session = self._create_session()
      rpc = session.get(self.msn_money.get_key_ratios_url(msn_stock_id), 
                        allow_redirects=True, 
                        timeout=DEFAULT_TIMEOUT,
                        hooks={
                          'response': self.parse_msn_money_ratios_data,
                        })
      self.rpcs.append(rpc)
      rpc = session.get(self.msn_money.get_quotes_url(msn_stock_id), 
                        allow_redirects=True, 
                        timeout=DEFAULT_TIMEOUT,
                        hooks={
                          'response': self.parse_msn_money_quotes_data,
                        })
      self.rpcs.append(rpc)
      rpc = session.get(self.msn_money.get_annual_statements_url(msn_stock_id), 
                        allow_redirects=True, 
                        timeout=DEFAULT_TIMEOUT,
                        hooks={
                          'response': self.parse_msn_money_annual_statement_data,
                        })
      self.rpcs.append(rpc)
    except Exception as e:
      logger.error(f"Error in continue_fetching_msn_money_data: {e}", exc_info=True)

  def parse_msn_money_overview_data(self, response, *args, **kwargs):
    try:
      if response.status_code != 200:
          logger.warning(f"MSN overview fetch failed: {response.status_code}")
          return
      
      if not self.msn_money:
          return
      
      result = response.text
      self.msn_money.parse_overview_data(result)
    except Exception as e:
      logger.error(f"Error parsing MSN overview data: {e}", exc_info=True)


  # Called asynchronously upon completion of the URL fetch from
  # `fetch_msn_money_data` and `continue_fetching_msn_money_data`.
  def parse_msn_money_ratios_data(self, response, *args, **kwargs):
    try:
      if response.status_code != 200:
        logger.warning(f"MSN ratios fetch failed: {response.status_code}")
        return
      if not self.msn_money:
        return
      result = response.text
      self.msn_money.parse_ratios_data(result)
    except Exception as e:
      logger.error(f"Error parsing MSN ratios data: {e}", exc_info=True)


  # Called asynchronously upon completion of the URL fetch from
  # `fetch_msn_money_data` and `continue_fetching_msn_money_data`.
  def parse_msn_money_quotes_data(self, response, *args, **kwargs):
    if response.status_code != 200:
      return
    if not self.msn_money:
      return
    result = response.text
    self.msn_money.parse_quotes_data(result)

  # Called asynchronously upon completion of the URL fetch from
  # `fetch_msn_money_data` and `continue_fetching_msn_money_data`.
  def parse_msn_money_annual_statement_data(self, response, *args, **kwargs):
    if response.status_code != 200:
      return
    if not self.msn_money:
      return
    result = response.text
    self.msn_money.parse_annual_report_data(result)

  def parse_msn_money_annual_financials_data(self, response, *args, **kwargs):
    try:
      if response.status_code != 200:
          logger.warning(f"MSN financials fetch failed: {response.status_code}")
          return
      
      if not self.msn_money:
          return
      
      result = response.text
      self.msn_money.parse_annual_financials_data(result)
    except Exception as e:
      logger.error(f"Error parsing MSN financials data: {e}", exc_info=True)


  def fetch_yahoo_finance_analysis(self):
    self.yahoo_finance_analysis = YahooFinanceAnalysis(self.ticker_symbol)
    session = self._create_session()
    rpc = session.get(self.yahoo_finance_analysis.url, 
                      allow_redirects=True, 
                      timeout=DEFAULT_TIMEOUT,
                      hooks={
                        'response': self.parse_yahoo_finance_analysis,
                      })
    self.rpcs.append(rpc)

  # Called asynchronously upon completion of the URL fetch from
  # `fetch_yahoo_finance_analysis`.
  def parse_yahoo_finance_analysis(self, response, *args, **kwargs):
    try:
      if response.status_code != 200:
        logger.warning(f"Yahoo Finance fetch failed: {response.status_code}")
        return
      if not self.yahoo_finance_analysis:
        return
      result = response.text
      success = self.yahoo_finance_analysis.parse_analyst_five_year_growth_rate(result)
      if not success:
        self.yahoo_finance_analysis = None
    except Exception as e:
      logger.error(f"Error parsing Yahoo Finance data: {e}", exc_info=True)


  def fetch_zacks_analysis(self):
    session = self._create_session()
    self.zacks_analysis = Zacks(self.ticker_symbol)

    rpc = session.get(
      self.zacks_analysis.url,
      allow_redirects=True,
      timeout=DEFAULT_TIMEOUT,
      hooks={
       'response': self.zacks_analysis.parse,
      }
    )
    self.rpcs.append(rpc)

  def parse_growth_rate_estimate(self, response, *args, **kwargs):
    try:
      if response.status_code != 200:
        logger.warning(f"Zacks fetch failed: {response.status_code}")
        return
      if not self.zacks_analysis:
        return
      result = response.text
      success = self.zacks_analysis.parse_analyst_five_year_growth_rate(result)
      if not success:
        self.zacks_analysis = None
    except Exception as e:
      logger.error(f"Error parsing Zacks data: {e}", exc_info=True)


  def fetch_yahoo_finance_chart(self):
    self.yahoo_finance_chart = YahooFinanceChart(self.ticker_symbol)
    session = self._create_session()
    rpc = session.get(self.yahoo_finance_chart.url, allow_redirects=True, hooks={
       'response': self.parse_yahoo_finance_chart,
    })
    self.rpcs.append(rpc)

  # Called asynchronously upon completion of the URL fetch from
  # `fetch_yahoo_finance_analysis`.
  def parse_yahoo_finance_chart(self, response, *args, **kwargs):
    if response.status_code != 200:
      return
    if not self.yahoo_finance_chart:
      return
    result = response.text
    success = self.yahoo_finance_chart.parse_chart(result)
    if not success:
      self.yahoo_finance_chart = None
