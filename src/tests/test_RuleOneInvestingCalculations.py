"""Tests for the isthisstockgood/RuleOneInvestingCalculations.py functions."""

import unittest
import isthisstockgood.RuleOneInvestingCalculations as RuleOne


class RuleOneInvestingCalculationsTest(unittest.TestCase):
    """Test suite for Rule One Investing calculation functions."""

    def test_compound_annual_growth_rate_increase(self):
        """Test CAGR with increasing values."""
        growth_rate = RuleOne.compound_annual_growth_rate(2805000, 108957000, 8)
        self.assertEqual(growth_rate, 58.0)

    def test_compound_annual_growth_rate_decrease(self):
        """Test CAGR with decreasing values."""
        growth_rate = RuleOne.compound_annual_growth_rate(108957000, 2805000, 8)
        self.assertEqual(growth_rate, -36.71)

    def test_compound_annual_growth_rate_single_negative_increasing(self):
        """Test CAGR with single negative value (increasing)."""
        growth_rate = RuleOne.compound_annual_growth_rate(-2805000, 108957000, 8)
        # This is an approximate since we can't really compute this value for a negative.
        self.assertEqual(growth_rate, 59.0)

    def test_compound_annual_growth_rate_single_negative_decreasing(self):
        """Test CAGR with single negative value (decreasing)."""
        growth_rate = RuleOne.compound_annual_growth_rate(2805000, -108957000, 8)
        # This is an approximate since we can't really compute this value for a negative.
        self.assertEqual(growth_rate, -58.51)

    def test_compound_annual_growth_rate_both_negative_decrease(self):
        """Test CAGR with both negative values (decreasing)."""
        growth_rate = RuleOne.compound_annual_growth_rate(-2805000, -108957000, 8)
        # We can't really compute negative growth rates, so this is the inverse
        # of the positive growth rate.
        self.assertEqual(growth_rate, -58.0)

    def test_compound_annual_growth_rate_both_negative_increase(self):
        """Test CAGR with both negative values (increasing)."""
        growth_rate = RuleOne.compound_annual_growth_rate(-108957000, -2805000, 8)
        # We can't really compute negative growth rates, so this is the inverse
        # of the positive growth rate.
        self.assertEqual(growth_rate, 36.71)

    def test_max_position_size(self):
        """Test maximum position size calculation."""
        share_price = 50.25
        trade_volume = 2134099
        max_position, max_shares = RuleOne.max_position_size(
            share_price, trade_volume
        )
        self.assertEqual(max_position, 1072335)
        self.assertEqual(max_shares, 21340)

    def test_payback_time(self):
        """Test payback time calculation."""
        years = RuleOne.payback_time(17680, 2115, 0.12)
        self.assertEqual(years, 6)

        # Test invalid inputs
        invalid_years = RuleOne.payback_time(17680, 2115, -0.12)
        self.assertEqual(invalid_years, -1)

        invalid_years = RuleOne.payback_time(17680, -2115, 0.12)
        self.assertEqual(invalid_years, -1)

    def test_calculate_estimated_future_price(self):
        """Test future price estimation."""
        future_price = RuleOne.calculate_estimated_future_price(1.25, 3)
        self.assertEqual(future_price, 3.75)

    def test_calculate_margin_of_safety(self):
        """Test margin of safety calculation."""
        default_margin_of_safety = RuleOne.calculate_margin_of_safety(100)
        self.assertEqual(default_margin_of_safety, 50)

        smaller_margin_of_safety = RuleOne.calculate_margin_of_safety(
            100, margin_of_safety=0.25
        )
        self.assertEqual(smaller_margin_of_safety, 75)

    def test_calculate_roic(self):
        """Test ROIC calculation."""
        expected_roic_history = [
            3.857280617164899,
            0.9852216748768473,
            0.199203187250996,
            0.20325203252032523,
            20.0
        ]

        net_income_history = [400, 200, 100, 50, 20]
        cash_history = [30, 200, 300, 500, 10]
        long_term_debt_history = [10000, 20000, 50000, 25000, 10]
        stockholder_equity_history = [400, 500, 500, 100, 100]

        for i in range(0, len(expected_roic_history)):
            roic_history = RuleOne.calculate_roic(
                net_income_history[i],
                cash_history[i],
                long_term_debt_history[i],
                stockholder_equity_history[i]
            )
            self.assertEqual(expected_roic_history[i], roic_history)


if __name__ == '__main__':
    unittest.main()
