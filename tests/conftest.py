import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from isthisstockgood.Active.MSNMoney import MSNMoney
from isthisstockgood.Active.alphavantage_client import AlphaVantageFundamentals
from isthisstockgood.Active.yfinance_client import YFinanceCompanyProfile
from isthisstockgood.DataFetcher import DataFetcher


class TestDataManager:
    """Load canned payloads used for deterministic tests."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def load_text(self, filename: str) -> str:
        path = self._data_dir / filename
        return path.read_text(encoding="utf-8")

    def load_json(self, filename: str):
        return json.loads(self.load_text(filename))


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def test_data_manager(test_data_dir: Path) -> TestDataManager:
    return TestDataManager(test_data_dir)


@pytest.fixture
def offline_data_fetcher(monkeypatch: pytest.MonkeyPatch, test_data_manager: TestDataManager):
    """Patch asynchronous fetchers to use static payloads for repeatable tests."""

    def _apply() -> None:
        profile_payload = test_data_manager.load_json("yfinance_profile.json")
        fundamentals_payload = test_data_manager.load_json("alphavantage_fundamentals.json")

        def fake_fetch_msn_money_data(self: DataFetcher) -> None:
            symbol = self.ticker_symbol.upper()
            if symbol != "MSFT":
                self.msn_money = None
                return

            profile = YFinanceCompanyProfile.from_payload(symbol, profile_payload)
            fundamentals = AlphaVantageFundamentals.from_payload(
                symbol,
                overview=fundamentals_payload["overview"],
                income_statement=fundamentals_payload["income_statement"],
                balance_sheet=fundamentals_payload["balance_sheet"],
                cash_flow=fundamentals_payload["cash_flow"],
                earnings=fundamentals_payload["earnings"],
                shares_override=profile.shares_outstanding,
            )
            self.msn_money = MSNMoney.from_sources(
                symbol,
                profile=profile,
                fundamentals=fundamentals,
            )

        monkeypatch.setattr(DataFetcher, "fetch_msn_money_data", fake_fetch_msn_money_data, raising=False)

    return _apply
