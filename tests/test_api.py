import json
from functools import partial

import pytest

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol
from isthisstockgood.config import AppConfig, configure_logger
from isthisstockgood.server import create_app


@pytest.fixture
def api_app(offline_data_fetcher):
    offline_data_fetcher()
    config = AppConfig(msn_money_api_key="test-key")
    logger = configure_logger(config.logger_name, config.log_level)
    fetcher = partial(fetch_data_for_ticker_symbol, user_agents=config.user_agents)
    return create_app(fetcher, config=config, logger=logger)


def test_import_app(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api')
        data = res.text
        assert json.loads(data) == {}
        assert res.status_code == 200


def test_get_data(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')
        assert res.status_code == 200

        data = res.json
        assert data['ticker'] == 'MSFT'
        assert data['name'] == 'Microsoft Corporation'
        assert data['sticker_price'] > 0.0
        assert data['payback_time'] > 0
        assert data['margin_of_safety_price'] > 0


def test_get_ten_cap_price(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')
        assert res.json['ten_cap_price'] == pytest.approx(52.0)


def test_ten_cap_price_has_two_places_precision(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')

        price = res.json['ten_cap_price']

        assert round(price, 2) == price


def test_invalid_ticker_is_rejected(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/api/ticker/INVALID!!!')
        assert res.status_code == 400
        assert res.json['error'] == 'Invalid ticker symbol'


def test_search_rejects_invalid_input(api_app):
    with api_app.test_client() as test_client:
        res = test_client.post('/search', data={'ticker': 'DROP TABLE'})
        assert res.status_code == 400
        assert res.json['error'] == 'Invalid ticker symbol'


def test_security_headers_present(api_app):
    with api_app.test_client() as test_client:
        res = test_client.get('/')
        assert res.headers['X-Content-Type-Options'] == 'nosniff'
        assert res.headers['X-Frame-Options'] == 'DENY'
        assert res.headers['Content-Security-Policy'] == "default-src 'self'"


@pytest.fixture
def cors_app(offline_data_fetcher):
    offline_data_fetcher()
    config = AppConfig(
        msn_money_api_key="test-key",
        cors_allow_origins=("https://example.com",),
    )
    logger = configure_logger(config.logger_name, config.log_level)
    fetcher = partial(fetch_data_for_ticker_symbol, user_agents=config.user_agents)
    return create_app(fetcher, config=config, logger=logger)


def test_cors_headers(cors_app):
    with cors_app.test_client() as test_client:
        res = test_client.get('/api', headers={'Origin': 'https://example.com'})
        assert res.headers['Access-Control-Allow-Origin'] == 'https://example.com'
        assert 'Access-Control-Allow-Methods' in res.headers


def test_unexpected_errors_are_sanitized(offline_data_fetcher):
    offline_data_fetcher()
    config = AppConfig(msn_money_api_key="test-key")
    logger = configure_logger(config.logger_name, config.log_level)

    def failing_fetcher(_: str):
        raise RuntimeError('Sensitive details should not leak')

    app = create_app(failing_fetcher, config=config, logger=logger)

    with app.test_client() as test_client:
        res = test_client.get('/api/ticker/msft')
        assert res.status_code == 500
        assert res.json == {'error': 'An unexpected error occurred.'}
