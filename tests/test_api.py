import json
from functools import partial

import pytest

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol
from isthisstockgood.config import AppConfig, configure_logger
from isthisstockgood.server import create_app


@pytest.fixture
def api_app(offline_data_fetcher):
    offline_data_fetcher()
    config = AppConfig()
    logger = configure_logger(config.logger_name, config.log_level)
    fetcher = partial(
        fetch_data_for_ticker_symbol,
        user_agents=config.user_agents,
        alpha_vantage_api_key=config.alpha_vantage_api_key,
    )
    return create_app(fetcher, config=config, logger=logger)


def test_import_app(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api')
        data = json.loads(res.data)
        assert data == {}
        assert res.status_code == 200


def test_get_data(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')
        assert res.status_code == 200

        data = res.get_json()
        assert data['ticker'] == 'MSFT'
        assert data['name'] == 'Microsoft Corporation'
        assert data['sticker_price'] > 0.0
        assert data['payback_time'] > 0
        assert data['margin_of_safety_price'] > 0


def test_get_ten_cap_price(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')
        assert res.get_json()['ten_cap_price'] == pytest.approx(92.0, rel=1e-4)


def test_ten_cap_price_has_two_places_precision(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')

        price = res.get_json()['ten_cap_price']

        assert round(price, 2) == price


def test_invalid_ticker_returns_404(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/unknown')
        assert res.status_code == 404
        body = res.get_json()
        assert body["error"] == "Invalid ticker symbol"
