import time

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol


def test_fetch_data_for_ticker_symbol_is_fast(offline_data_fetcher):
    offline_data_fetcher()
    start = time.perf_counter()
    iterations = 10

    for _ in range(iterations):
        result = fetch_data_for_ticker_symbol('msft')
        assert result is not None

    duration = time.perf_counter() - start
    average = duration / iterations

    assert average < 0.02, f"Average fetch duration {average:.5f}s exceeds performance budget"
