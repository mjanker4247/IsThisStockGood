"""Unit tests for the payback time helper in ``DataFetcher``."""

from isthisstockgood.DataFetcher import _calculate_payback_time


def test_calculate_payback_time_accepts_zero_growth_rate():
    """Analyst growth rate of zero should still yield a finite payback period."""

    years = _calculate_payback_time(
        one_year_equity_growth_rate=12.0,
        last_year_net_income=2_000_000,
        market_cap=15_000_000,
        analyst_five_year_growth_rate=0,
    )

    assert years == 8


def test_calculate_payback_time_returns_none_for_missing_inputs():
    """Empty or ``None`` inputs should result in no payback time."""

    assert _calculate_payback_time(None, 1, 1, 1) is None
    assert _calculate_payback_time(10, None, 1, 1) is None
    assert _calculate_payback_time(10, 1, "", 1) is None


def test_calculate_payback_time_handles_invalid_growth():
    """Negative blended growth rates from upstream data should be ignored."""

    assert _calculate_payback_time(5.0, 1_000_000, 5_000_000, -12.0) is None
