"""Tests for Yahoo Finance world indices ticker extraction."""

from __future__ import annotations

from urllib.parse import quote

import pandas as pd
import pytest
import requests

from magic_formula.world_indices_fetcher import (
    INDEX_COMPONENTS_URL_TEMPLATE,
    WORLD_INDICES_URL,
    YahooWorldIndicesClient,
    YahooWorldIndicesError,
    build_world_index_ticker_list,
)


class FakeResponse:
    """Lightweight stand-in for :class:`requests.Response`."""

    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_fetch_indices_parses_symbols(monkeypatch):
    """Client should parse index metadata from the screener payload."""

    payload = {
        "finance": {
            "result": [
                {
                    "quotes": [
                        {"symbol": "^AAA", "shortName": "Alpha Index"},
                        {"symbol": "^BBB", "longName": "Beta Index"},
                    ]
                }
            ],
            "error": None,
        }
    }

    def fake_get(self, url, headers=None, timeout=None):  # noqa: D401 - signature matches requests
        assert url == WORLD_INDICES_URL
        return FakeResponse(payload)

    monkeypatch.setattr(requests.Session, "get", fake_get)

    client = YahooWorldIndicesClient()
    indices = client.fetch_indices()

    assert [index.symbol for index in indices] == ["^AAA", "^BBB"]
    assert [index.name for index in indices] == ["Alpha Index", "Beta Index"]


def test_fetch_indices_missing_results_raises(monkeypatch):
    """Invalid payloads should trigger an explicit error."""

    payload = {"finance": {"result": []}}

    def fake_get(self, url, headers=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(requests.Session, "get", fake_get)

    client = YahooWorldIndicesClient()

    with pytest.raises(YahooWorldIndicesError):
        client.fetch_indices()


def test_build_world_index_ticker_list_returns_unique_tickers(monkeypatch):
    """End-to-end collection removes duplicates per index and overall."""

    world_indices_payload = {
        "finance": {
            "result": [
                {
                    "quotes": [
                        {"symbol": "^AAA", "shortName": "Alpha Index"},
                        {"symbol": "^BBB", "shortName": "Beta Index"},
                    ]
                }
            ],
            "error": None,
        }
    }

    component_payloads = {
        "^AAA": {
            "quoteSummary": {
                "result": [
                    {
                        "components": {
                            "components": [
                                {"symbol": "AAA1", "name": "AAA One"},
                                {"symbol": "AAA2", "name": "AAA Two"},
                            ]
                        }
                    }
                ],
                "error": None,
            }
        },
        "^BBB": {
            "quoteSummary": {
                "result": [
                    {
                        "components": {
                            "components": [
                                {"symbol": "AAA1", "name": "AAA One"},
                                {"symbol": "BBB1", "name": "BBB One"},
                                {"symbol": "AAA1", "name": "AAA One"},
                            ]
                        }
                    }
                ],
                "error": None,
            }
        },
    }

    def fake_get(self, url, headers=None, timeout=None):
        if url == WORLD_INDICES_URL:
            return FakeResponse(world_indices_payload)

        for index_symbol, payload in component_payloads.items():
            expected_url = INDEX_COMPONENTS_URL_TEMPLATE.format(symbol=quote(index_symbol, safe=""))
            if url == expected_url:
                return FakeResponse(payload)

        raise AssertionError(f"Unexpected URL requested: {url}")

    monkeypatch.setattr(requests.Session, "get", fake_get)

    client = YahooWorldIndicesClient()
    per_index_df, unique_df = build_world_index_ticker_list(client)

    assert list(per_index_df.columns) == ["IndexSymbol", "IndexName", "Ticker", "Company"]
    assert len(per_index_df) == 4
    assert per_index_df[per_index_df["IndexSymbol"] == "^AAA"]["Ticker"].tolist() == [
        "AAA1",
        "AAA2",
    ]
    assert per_index_df[per_index_df["IndexSymbol"] == "^BBB"]["Ticker"].tolist() == [
        "AAA1",
        "BBB1",
    ]

    assert set(unique_df["Ticker"].tolist()) == {"AAA1", "AAA2", "BBB1"}
    assert unique_df.loc[unique_df["Ticker"] == "AAA1", "Company"].iloc[0] == "AAA One"
    assert isinstance(per_index_df, pd.DataFrame)
    assert isinstance(unique_df, pd.DataFrame)
