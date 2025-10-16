"""Tests for the RuleOneInvestingCalculations module."""


import math
import unittest

import isthisstockgood.RuleOneInvestingCalculations as RuleOne


class RuleOneInvestingCalculationsTest(unittest.TestCase):

  def test_compound_annual_growth_rate_increase(self):
    growth_rate = RuleOne.compound_annual_growth_rate(2805000, 108957000, 8)
    self.assertEqual(growth_rate, 58.0)

  def test_compound_annual_growth_rate_decrease(self):
    growth_rate = RuleOne.compound_annual_growth_rate(108957000, 2805000, 8)
    self.assertEqual(growth_rate, -36.71)

  def test_compound_annual_growth_rate_both_negative_decrease(self):
    growth_rate = RuleOne.compound_annual_growth_rate(-2805000, -108957000, 8)
    self.assertEqual(growth_rate, -58.0)

  def test_compound_annual_growth_rate_both_negative_increase(self):
    growth_rate = RuleOne.compound_annual_growth_rate(-108957000, -2805000, 8)
    self.assertEqual(growth_rate, 36.71)

  def test_compound_annual_growth_rate_invalid_inputs(self):
    with self.assertRaises(ValueError):
      RuleOne.compound_annual_growth_rate(0, 100, 5)
    with self.assertRaises(ValueError):
      RuleOne.compound_annual_growth_rate(100, 0, 0)
    with self.assertRaises(ValueError):
      RuleOne.compound_annual_growth_rate(-100, 100, 5)

  def test_slope_of_best_fit_line_for_data(self):
    data = [1.3, 2.5, 3.5, 8.5]
    slope = RuleOne.slope_of_best_fit_line_for_data(data)
    self.assertEqual(slope, 2.26)

  def test_slope_of_best_fit_line_requires_two_values(self):
    with self.assertRaises(ValueError):
      RuleOne.slope_of_best_fit_line_for_data([1.5])

  def test_max_position_size(self):
    share_price = 50.25
    trade_volume = 2134099
    max_position, max_shares = RuleOne.max_position_size(share_price, trade_volume)
    self.assertEqual(max_position, 1072335)
    self.assertEqual(max_shares, 21340)

  def test_max_position_size_invalid_inputs(self):
    with self.assertRaises(ValueError):
      RuleOne.max_position_size(0, 100)
    with self.assertRaises(ValueError):
      RuleOne.max_position_size(10, -100)

  def test_payback_time(self):
    years = RuleOne.payback_time(17680, 2115, 0.12)
    self.assertEqual(years, 6)

  def test_payback_time_zero_growth(self):
    years = RuleOne.payback_time(1000, 100, 0)
    self.assertEqual(years, 10)

  def test_payback_time_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.payback_time(17680, 2115, -0.12)
    with self.assertRaises(ValueError):
      RuleOne.payback_time(17680, -2115, 0.12)

  def test_rule_one_margin_of_safety_price(self):
    margin_of_safety, sticker_price = RuleOne.margin_of_safety_price(
      5.0, 0.12, 10.0, 20.0
    )
    expected_future_eps = RuleOne.calculate_future_eps(5.0, 0.12)
    expected_future_pe = RuleOne.calculate_future_pe(0.12, 10.0, 20.0)
    expected_future_price = RuleOne.calculate_estimated_future_price(
      expected_future_eps, expected_future_pe
    )
    expected_sticker_price = RuleOne.calculate_sticker_price(expected_future_price)
    self.assertAlmostEqual(sticker_price, expected_sticker_price)
    self.assertAlmostEqual(margin_of_safety, RuleOne.calculate_margin_of_safety(expected_sticker_price))

  def test_margin_of_safety_price_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.margin_of_safety_price(5.0, 0.12, 0, 20.0)
    with self.assertRaises(ValueError):
      RuleOne.margin_of_safety_price(5.0, 0.12, 20.0, 10.0)

  def test_calculate_future_eps(self):
    future_eps = RuleOne.calculate_future_eps(5.0, 0.12, 10)
    self.assertAlmostEqual(future_eps, 5.0 * math.pow(1.12, 10))

  def test_calculate_future_eps_negative_growth(self):
    future_eps = RuleOne.calculate_future_eps(5.0, -0.05, 10)
    self.assertAlmostEqual(future_eps, 5.0 * math.pow(0.95, 10))

  def test_calculate_future_eps_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_future_eps(5.0, 0.1, 0)

  def test_calculate_future_pe(self):
    future_pe = RuleOne.calculate_future_pe(0.12, 10.0, 20.0)
    self.assertEqual(future_pe, 15.0)

  def test_calculate_future_pe_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_future_pe(0.12, 0, 20.0)
    with self.assertRaises(ValueError):
      RuleOne.calculate_future_pe(0.12, 20.0, 10.0)
    with self.assertRaises(ValueError):
      RuleOne.calculate_future_pe(-0.05, 10.0, 20.0)

  def test_calculate_estimated_future_price(self):
    future_price = RuleOne.calculate_estimated_future_price(1.25, 3)
    self.assertEqual(future_price, 3.75)

  def test_calculate_estimated_future_price_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_estimated_future_price("invalid", 3)

  def test_calculate_sticker_price(self):
    future_price = 150.0
    sticker_price = RuleOne.calculate_sticker_price(future_price, 10, 0.15)
    expected = future_price / math.pow(1.15, 10)
    self.assertAlmostEqual(sticker_price, expected)

  def test_calculate_sticker_price_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_sticker_price(150.0, 0, 0.15)
    with self.assertRaises(ValueError):
      RuleOne.calculate_sticker_price(150.0, 10, -1.5)

  def test_calculate_margin_of_safety(self):
    default_margin_of_safety = RuleOne.calculate_margin_of_safety(100)
    self.assertEqual(default_margin_of_safety, 50)

    smaller_margin_of_safety = RuleOne.calculate_margin_of_safety(100, margin_of_safety=0.25)
    self.assertEqual(smaller_margin_of_safety, 75)

  def test_calculate_margin_of_safety_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_margin_of_safety(0)
    with self.assertRaises(ValueError):
      RuleOne.calculate_margin_of_safety(100, margin_of_safety=1.5)

  def test_calculate_roic(self):
    expected_roic_history = [
        3.857280617164899, 0.9852216748768473, 0.199203187250996, 0.20325203252032523, 20.0
    ]
    net_income_history = [400, 200, 100, 50, 20]
    cash_history = [30, 200, 300, 500, 10]
    long_term_debt_history = [10000, 20000, 50000, 25000, 10]
    stockholder_equity_history = [400, 500, 500, 100, 100]
    for i in range(0, len(expected_roic_history)):
      roic_history = RuleOne.calculate_roic(
        net_income_history[i], cash_history[i],
        long_term_debt_history[i], stockholder_equity_history[i]
      )
      self.assertEqual(expected_roic_history[i], roic_history)

  def test_calculate_roic_invalid(self):
    with self.assertRaises(ValueError):
      RuleOne.calculate_roic(100, 50, 25, 25)
