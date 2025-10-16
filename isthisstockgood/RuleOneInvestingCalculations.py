"""A collection of functions to compute investing calculations from Rule #1."""

from __future__ import division

import math


def _ensure_numeric(value, name):
  """Validate that *value* can be represented as a float."""
  if value is None:
    raise ValueError(f"{name} must not be None.")
  try:
    return float(value)
  except (TypeError, ValueError):
    raise ValueError(f"{name} must be a numeric value.")


def _ensure_positive(value, name, allow_zero=False):
  """Validate that *value* is positive (or zero when allowed)."""
  numeric_value = _ensure_numeric(value, name)
  if allow_zero and numeric_value == 0:
    return numeric_value
  if numeric_value <= 0:
    raise ValueError(f"{name} must be greater than 0.")
  return numeric_value


def compound_annual_growth_rate(start_balance, end_balance, years):
  """
  Returns the compound annual growth rate from raw data.

  Formula = (end/start)^(1/years) - 1
  """
  start = _ensure_numeric(start_balance, "start_balance")
  end = _ensure_numeric(end_balance, "end_balance")
  years_value = _ensure_numeric(years, "years")
  if years_value <= 0:
    raise ValueError("years must be greater than 0.")
  if start == 0:
    raise ValueError("start_balance must not be 0.")
  if start * end < 0:
    raise ValueError("start_balance and end_balance must not have opposing signs.")

  exponent = 1.0 / years_value
  ratio = end / start
  if ratio < 0:
    raise ValueError("Unable to compute CAGR for negative ratios.")

  growth_rate = pow(ratio if ratio != 0 else 0.0, exponent) - 1.0
  if end < start:
    growth_rate = -abs(growth_rate)
  else:
    growth_rate = abs(growth_rate)
  return round(growth_rate * 100, 2)


def slope_of_best_fit_line_for_data(data):
  """
  Returns the slope of the line of best fit for a set of data points.

  Args:
    data: A list of data points to plot a best-fit line on.

  Returns:
    Returns the slope of the best fit line.
  """
  if data is None:
    raise ValueError("data must not be None.")
  if isinstance(data, (str, bytes)):
    raise ValueError("data must be an iterable of numeric values.")
  values = list(data)
  if len(values) < 2:
    raise ValueError("At least two data points are required to compute a slope.")

  y_values = [
    _ensure_numeric(point, f"data[{index}]") for index, point in enumerate(values)
  ]
  x_values = list(range(len(y_values)))
  x_mean = sum(x_values) / len(x_values)
  y_mean = sum(y_values) / len(y_values)

  numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
  denominator = sum((x - x_mean) ** 2 for x in x_values)
  if denominator == 0:
    raise ValueError("Unable to compute slope when all x values are identical.")
  slope = numerator / denominator
  return round(slope, 2)


def max_position_size(share_price, trade_volume):
  """
  Returns the limits for a position size for a given stock. These are the
  value to limit your position below to make sure you can buy in or sell out of
  a stock without causing an artifical price change.

  This boils down to 1% of the volume or 1% of the price of the volume.

  Args:
    share_price: The share price of the stock.
    trade_volume: The average trade volume of the stock.
  """
  share_price_value = _ensure_positive(share_price, "share_price")
  trade_volume_value = _ensure_positive(trade_volume, "trade_volume")
  max_shares = math.floor(trade_volume_value * 0.01)  # 1%
  max_position = math.floor(share_price_value * max_shares)
  return max_position,max_shares


def payback_time(market_cap, net_income, estimated_growth_rate):
  """
  Determine the amount of years to get your money back if you were to buy the
  entire company at the current market cap given the TTM net income and
  expected growth rate.

  For more details, read PaybackTime by Phil Town for information on this
  calculation. Basically its the summation of each years future value (FV
  function on excel).

  Args:
   market_cap: The current market capitalization for the company.
   net_income: The trailing twelve month (TTM) net income for the company.
   estimated_growth_rate: A conservative estimated growth rate. (Typically the
       minimum of a professional growth estimate and the historical growth rate
       of equity/book-value-per-share.)

  Returns:
    Returns the number of years (rounded up) for how many years are needed to
    receive a 100% return on your investment based on the company's income. If
    any of the inputs are invalid, returns -1.
  """
  market_cap_value = _ensure_positive(market_cap, "market_cap")
  net_income_value = _ensure_positive(net_income, "net_income")
  growth_rate_value = _ensure_numeric(estimated_growth_rate, "estimated_growth_rate")
  if growth_rate_value < 0:
    raise ValueError("estimated_growth_rate must be greater than or equal to 0.")

  yearly_income = net_income_value
  total_payback = 0
  years = 0
  while total_payback < market_cap_value:
    yearly_income += yearly_income * growth_rate_value
    total_payback += yearly_income
    years += 1
    if years > 10_000:
      raise ValueError("Payback period did not converge within a reasonable timeframe.")

  return years


def margin_of_safety_price(current_eps, estimated_growth_rate,
                           historical_low_pe, historical_high_pe):
  """
  Calculates the value a stock should be purchased at today to have a 50% margin
  of safety given a 10 year timeframe with a minimum projection of 15%-per-year
  earnings.

  Args:
    current_eps: The current Earnings Per Share (EPS) value of the stock.
        Typically found from Yahoo Finance or Wall Street Journal page.
    estimated_growth_rate: A conservative estimated growth rate. (Typically the
        minimum of a professional growth estimate and the historical growth
        rate of equity/book-value-per-share.)
    historical_low_pe: The 5-year low for the price-to-earnings (PE) ratio.
        Usually found on MSN Money.
    historical_high_pe: The 5-year high for the price-to-earnings (PE) ratio.
        Usually found on MSN Money.

  Returns:
     1. The maximum price to buy the stock for with a 50% margin of safety.
     2. The sticker price, which is the estimated fair-value price today. This
        value can be used to determine when is a good time to exit a position
        after a big run-up in price.
  """
  current_eps_value = _ensure_positive(current_eps, "current_eps")
  estimated_growth_rate_value = _ensure_numeric(estimated_growth_rate, "estimated_growth_rate")
  if estimated_growth_rate_value < -1:
    raise ValueError("estimated_growth_rate must be greater than -100%.")
  historical_low_pe_value = _ensure_positive(historical_low_pe, "historical_low_pe")
  historical_high_pe_value = _ensure_positive(historical_high_pe, "historical_high_pe")
  if historical_high_pe_value < historical_low_pe_value:
    raise ValueError("historical_high_pe must be greater than or equal to historical_low_pe.")

  future_eps = calculate_future_eps(current_eps_value, estimated_growth_rate_value)
  future_pe = calculate_future_pe(estimated_growth_rate_value, historical_low_pe_value,
                                  historical_high_pe_value)
  future_price = calculate_estimated_future_price(future_eps, future_pe)
  sticker_price = calculate_sticker_price(future_price)
  margin_of_safety = calculate_margin_of_safety(sticker_price)
  return margin_of_safety, sticker_price


def calculate_future_eps(current_eps, estimated_growth_rate, time_horizon=10):
  """
  Calculates the estimated future earnings-per-share (EPS) value in 10 years.

  This implements the same underlying formula as the Excel "FV" (future value)
  function.

  Args:
    current_eps: The current Earnings Per Share (EPS) value of the stock.
        Typically found from Yahoo Finance or Wall Street Journal page.
    estimated_growth_rate: A conservative estimated growth rate. (Typically the
        minimum of a professional growth estimate and the historical growth
        rate of equity/book-value-per-share.)
    time_horizon: The desired time horizon to calculate for. Defaults to 10.

  Returns:
    The estimated future earnings-per-share value in 10 years time.
  """
  # FV = C * (1 + r)^n
  # where C -> current_value, r -> rate, n -> years
  current_eps_value = _ensure_numeric(current_eps, "current_eps")
  estimated_growth_rate_value = _ensure_numeric(estimated_growth_rate, "estimated_growth_rate")
  time_horizon_value = _ensure_numeric(time_horizon, "time_horizon")
  if time_horizon_value <= 0:
    raise ValueError("time_horizon must be greater than 0.")
  ten_year_growth_rate = math.pow(1.0 + estimated_growth_rate_value, time_horizon_value)
  future_eps_value = current_eps_value * ten_year_growth_rate
  return future_eps_value


def calculate_future_pe(estimated_growth_rate, historical_low_pe,
                        historical_high_pe):
  """
  Calculates the future price-to-earnings (PE) ratio value.

  Args:
    estimated_growth_rate: A conservative estimated growth rate. (Typically the
        minimum of a professional growth estimate and the historical growth
        rate of equity/book-value-per-share.)
    historical_low_pe: The 5-year low for the price-to-earnings (PE) ratio.
        Usually found on MSN Money.
    historical_high_pe: The 5-year high for the price-to-earnings (PE) ratio.
        Usually found on MSN Money.

  Returns:
    The estimated future price-to-earnings ratio.
  """
  # To be conservative, we will take the smaller of these two: 1. the average
  # historical PE, 2. double the estimated growth rate.
  estimated_growth_rate_value = _ensure_numeric(estimated_growth_rate, "estimated_growth_rate")
  historical_low_pe_value = _ensure_positive(historical_low_pe, "historical_low_pe")
  historical_high_pe_value = _ensure_positive(historical_high_pe, "historical_high_pe")
  if historical_high_pe_value < historical_low_pe_value:
    raise ValueError("historical_high_pe must be greater than or equal to historical_low_pe.")
  future_pe_one = (historical_low_pe_value + historical_high_pe_value) / 2.0
  # Multiply the growth rate by 100 to convert from a decimal to a percent.
  future_pe_two = 2.0 * (estimated_growth_rate_value * 100.0)
  conservative_future_pe = min(future_pe_one, future_pe_two)
  if conservative_future_pe <= 0:
    raise ValueError("Calculated future PE must be greater than 0.")
  return conservative_future_pe


def calculate_estimated_future_price(future_eps, future_pe):
  """
  Calculates the estimated future price of a stock.

  Args:
    future_eps: A future earnings-per-share (EPS) value, typically on a
        10-year time horizon.
    future_pe: A future price-to-earnings (PE) value.

  Returns:
    The estimated future price of a stock.
  """
  future_eps_value = _ensure_numeric(future_eps, "future_eps")
  future_pe_value = _ensure_numeric(future_pe, "future_pe")
  return future_eps_value * future_pe_value


def calculate_sticker_price(future_price, time_horizon=10,
                            rate_of_return=0.15):
  """
  Calculates the sticker price of a stock given its estimated future price and
  a desired rate of return.

  This implements the underlying formula as the Excel "PV" (present value)
  function.

  Args:
    future_price: The estimated future price of a stock.
    time_horizon: The desired time horizon to calculate for. Defaults to 10.
    rate_of_return: The desired minimum rate of return.

  Returns:
    The calculated sticker price.
  """
  # PV = FV / (1 + r)^n
  # where r -> rate and n -> years
  future_price_value = _ensure_positive(future_price, "future_price")
  time_horizon_value = _ensure_numeric(time_horizon, "time_horizon")
  rate_of_return_value = _ensure_numeric(rate_of_return, "rate_of_return")
  if time_horizon_value <= 0:
    raise ValueError("time_horizon must be greater than 0.")
  if rate_of_return_value <= -1:
    raise ValueError("rate_of_return must be greater than -100%.")
  target_growth_rate = math.pow(1.0 + rate_of_return_value, time_horizon_value)
  sticker_price = future_price_value / target_growth_rate
  return sticker_price


def calculate_margin_of_safety(sticker_price, margin_of_safety=0.5):
  """
  Calculates a margin of safety price for a stock.

  Args:
    sticker_price: The sticker price of a stock.
    margin_of_safety: The desired margin of safety as a percentage. Defaults to
        0.5 (i.e. 50%).

  Returns:
    The margin of safety price.
  """
  sticker_price_value = _ensure_positive(sticker_price, "sticker_price")
  margin_of_safety_value = _ensure_numeric(margin_of_safety, "margin_of_safety")
  if not 0 <= margin_of_safety_value <= 1:
    raise ValueError("margin_of_safety must be between 0 and 1 inclusive.")
  return sticker_price_value * (1 - margin_of_safety_value)

def calculate_roic(net_income, cash, long_term_debt, stockholder_equity):
  net_income_value = _ensure_numeric(net_income, "net_income")
  cash_value = _ensure_numeric(cash, "cash")
  long_term_debt_value = _ensure_numeric(long_term_debt, "long_term_debt")
  stockholder_equity_value = _ensure_numeric(stockholder_equity, "stockholder_equity")
  invested_capital = stockholder_equity_value + long_term_debt_value - cash_value
  if invested_capital <= 0:
    raise ValueError("Invested capital must be greater than 0.")
  return (net_income_value / invested_capital) * 100
