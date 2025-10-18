"""Download unique ticker symbols from Yahoo Finance world indices."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from urllib.parse import quote

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

WORLD_INDICES_URL = (
    "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    "?scrIds=world_indices&count=250"
)
INDEX_COMPONENTS_URL_TEMPLATE = (
    "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=components"
)
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (IsThisStockGood/WorldIndicesFetcher)",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
}
REQUEST_TIMEOUT = 10


class YahooWorldIndicesError(RuntimeError):
    """Raised when Yahoo Finance responses cannot be processed."""


@dataclass(frozen=True)
class WorldIndex:
    """Metadata describing a Yahoo Finance world index."""

    symbol: str
    name: str


@dataclass(frozen=True)
class IndexConstituent:
    """Represents a single component of a world index."""

    symbol: str
    name: str


class YahooWorldIndicesClient:
    """Client responsible for retrieving world indices and their components."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def _get_json(self, url: str) -> dict:
        """Perform a GET request and return the JSON payload."""

        try:
            response = self._session.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - exercised via unit tests
            raise YahooWorldIndicesError(f"Failed to fetch data from {url}") from exc

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - exercised via unit tests
            raise YahooWorldIndicesError(f"Invalid JSON payload received from {url}") from exc

    def fetch_indices(self) -> List[WorldIndex]:
        """Return metadata for all Yahoo Finance world indices."""

        payload = self._get_json(WORLD_INDICES_URL)

        try:
            results = payload["finance"]["result"]
        except (KeyError, TypeError) as exc:
            raise YahooWorldIndicesError("Indices payload missing finance.result") from exc

        if not results:
            raise YahooWorldIndicesError("Indices payload did not contain any results")

        quotes = results[0].get("quotes", [])
        indices: List[WorldIndex] = []
        for entry in quotes:
            symbol = (entry.get("symbol") or "").strip()
            if not symbol:
                continue
            name = (
                entry.get("longName")
                or entry.get("shortName")
                or entry.get("fullExchangeName")
                or symbol
            )
            indices.append(WorldIndex(symbol=symbol, name=str(name).strip()))

        if not indices:
            raise YahooWorldIndicesError("No index symbols were returned from Yahoo Finance")

        return indices

    def fetch_constituents(self, index_symbol: str) -> List[IndexConstituent]:
        """Return the unique ticker symbols for a specific world index."""

        encoded_symbol = quote(index_symbol, safe="")
        url = INDEX_COMPONENTS_URL_TEMPLATE.format(symbol=encoded_symbol)
        payload = self._get_json(url)

        components_root = (
            payload.get("quoteSummary", {})
            .get("result", [{}])[0]
            .get("components", {})
        )
        raw_components = (
            components_root.get("components")
            or components_root.get("constituents")
            or []
        )

        unique_components: dict[str, IndexConstituent] = {}
        for entry in raw_components:
            symbol = (entry.get("symbol") or "").strip()
            if not symbol:
                continue
            name = str(entry.get("name") or entry.get("shortName") or "").strip()
            normalized_symbol = symbol.upper()
            if normalized_symbol not in unique_components:
                unique_components[normalized_symbol] = IndexConstituent(
                    symbol=normalized_symbol,
                    name=name,
                )

        if not unique_components:
            LOGGER.warning("No components returned for index %s", index_symbol)

        return list(unique_components.values())


def build_world_index_ticker_list(
    client: YahooWorldIndicesClient | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Collect per-index and unique ticker data for world indices."""

    client = client or YahooWorldIndicesClient()
    indices = client.fetch_indices()

    records = []
    for index in indices:
        constituents = client.fetch_constituents(index.symbol)
        for component in constituents:
            records.append(
                {
                    "IndexSymbol": index.symbol,
                    "IndexName": index.name,
                    "Ticker": component.symbol,
                    "Company": component.name,
                }
            )

    if not records:
        raise YahooWorldIndicesError("No components retrieved for any indices")

    per_index_df = pd.DataFrame.from_records(records)
    per_index_df.drop_duplicates(subset=["IndexSymbol", "Ticker"], inplace=True)
    per_index_df.sort_values(["IndexSymbol", "Ticker"], inplace=True)
    per_index_df.reset_index(drop=True, inplace=True)

    unique_df = (
        per_index_df.drop_duplicates(subset=["Ticker"])
        .sort_values(["Ticker"])
        .reset_index(drop=True)
    )

    return per_index_df, unique_df


def save_world_index_ticker_list(output_dir: Path | None = None) -> Tuple[Path, Path]:
    """Persist per-index and unique ticker CSV files to ``output_dir``."""

    output_dir = Path("." if output_dir is None else output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    per_index_df, unique_df = build_world_index_ticker_list()

    per_index_path = output_dir / "world_indices_components.csv"
    unique_path = output_dir / "world_indices_unique_tickers.csv"

    per_index_df.to_csv(per_index_path, index=False)
    unique_df.to_csv(unique_path, index=False)

    LOGGER.info("Saved %d per-index rows to %s", len(per_index_df), per_index_path)
    LOGGER.info("Saved %d unique tickers to %s", len(unique_df), unique_path)

    return per_index_path, unique_path


def main() -> None:
    """Command-line entry point."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    save_world_index_ticker_list()


if __name__ == "__main__":
    main()
