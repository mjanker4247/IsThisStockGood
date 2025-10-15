from unittest.mock import Mock, patch

from isthisstockgood.IdentifierResolver import IdentifierResolution, resolve_identifier


def test_isin_resolution_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "quotes": [
            {"symbol": "BAS.DE", "quoteType": "EQUITY"},
        ]
    }

    with patch("isthisstockgood.IdentifierResolver.requests.get", return_value=mock_response) as mock_get:
        resolution = resolve_identifier("DE000BASF111")

    mock_get.assert_called_once()
    assert isinstance(resolution, IdentifierResolution)
    assert resolution.identifier_type == "isin"
    assert resolution.successful is True
    assert resolution.symbol == "BAS.DE"
    assert resolution.input_identifier == "DE000BASF111"


def test_isin_resolution_failure_returns_none_symbol():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"quotes": []}

    with patch("isthisstockgood.IdentifierResolver.requests.get", return_value=mock_response):
        resolution = resolve_identifier("DE000FAKE000")

    assert resolution.identifier_type == "isin"
    assert resolution.successful is False
    assert resolution.symbol == "DE000FAKE000"


def test_ticker_passthrough():
    resolution = resolve_identifier("NVDA")

    assert resolution.identifier_type == "ticker"
    assert resolution.successful is True
    assert resolution.symbol == "NVDA"
