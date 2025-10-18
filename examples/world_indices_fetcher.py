#!/usr/bin/env python3
"""Example CLI demonstrating the Yahoo Finance world indices fetcher."""

from __future__ import annotations

from magic_formula.world_indices_fetcher import (
    YahooWorldIndicesClient,
    YahooWorldIndicesError,
    build_world_index_ticker_list,
)


def main() -> None:
    """Fetch indices and display a short summary in the console."""

    client = YahooWorldIndicesClient()

    try:
        indices = client.fetch_indices()
    except YahooWorldIndicesError as exc:  # pragma: no cover - network dependent
        print(f"Failed to fetch world indices: {exc}")
        return

    print(f"Fetched {len(indices)} world indices from Yahoo Finance.")
    for index in indices[:5]:
        print(f" - {index.symbol}: {index.name}")
    if len(indices) > 5:
        print("   ...")

    try:
        per_index_df, unique_df = build_world_index_ticker_list(client)
    except YahooWorldIndicesError as exc:  # pragma: no cover - network dependent
        print(f"Failed to fetch index constituents: {exc}")
        return

    print(
        "
Summary: "
        f"{len(unique_df)} unique tickers across {len(per_index_df)} index components."
    )
    print("Sample constituents:")
    for row in per_index_df.head(10).itertuples(index=False):
        company = row.Company or "Unknown"
        print(f" {row.IndexSymbol:>8} -> {row.Ticker:<8} {company}")

    print(
        "
Use magic_formula.world_indices_fetcher.save_world_index_ticker_list() "
        "to export the data to CSV files."
    )


if __name__ == "__main__":
    main()
