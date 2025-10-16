import json
from functools import partial

from isthisstockgood.DataFetcher import fetch_data_for_ticker_symbol
from isthisstockgood.config import AppConfig, configure_logger
from isthisstockgood.server import create_app


def _create_app():
    config = AppConfig()
    logger = configure_logger(config.logger_name, config.log_level)
    fetcher = partial(fetch_data_for_ticker_symbol, user_agents=config.user_agents)
    return create_app(fetcher, config=config, logger=logger)


def test_import_app():
    app = _create_app()

    with app.test_client() as test_client:
        res = test_client.get('/api')
        data = res.text
        assert json.loads(data) == {}
        assert res.status_code == 200


def test_get_data():
    app = _create_app()

    with app.test_client() as test_client:
        res = test_client.get('/api/ticker/nvda')
        assert res.status_code == 200

        data = res.json
        assert data['debt_payoff_time'] >= 0
        assert data['sticker_price'] > 0.0
        assert data['payback_time'] > 1


def test_get_ten_cap_price():
    app = _create_app()

    with app.test_client() as test_client:
        res = test_client.get('/api/ticker/nvda')
        assert res.json['ten_cap_price'] > 0


def test_ten_cap_price_has_two_places_precision():
    app = _create_app()

    with app.test_client() as test_client:
        res = test_client.get('/api/ticker/nvda')

        price = res.json['ten_cap_price']

        assert round(price, 2) == price
