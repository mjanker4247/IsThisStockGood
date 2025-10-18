"""Backwards compatibility layer for world indices utilities.

Prefer :mod:`magic_formula.world_indices_fetcher` for new code.
"""

from __future__ import annotations

from .world_indices_fetcher import (
    DEFAULT_HEADERS,
    INDEX_COMPONENTS_URL_TEMPLATE,
    REQUEST_TIMEOUT,
    WORLD_INDICES_URL,
    IndexConstituent,
    WorldIndex,
    YahooWorldIndicesClient,
    YahooWorldIndicesError,
    build_world_index_ticker_list,
    main,
    save_world_index_ticker_list,
)

__all__ = [
    "DEFAULT_HEADERS",
    "INDEX_COMPONENTS_URL_TEMPLATE",
    "REQUEST_TIMEOUT",
    "WORLD_INDICES_URL",
    "IndexConstituent",
    "WorldIndex",
    "YahooWorldIndicesClient",
    "YahooWorldIndicesError",
    "build_world_index_ticker_list",
    "main",
    "save_world_index_ticker_list",
]
