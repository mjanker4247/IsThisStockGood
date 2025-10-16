import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from isthisstockgood.Active.MSNMoney import MSNMoney
from isthisstockgood.Active.YahooFinance import YahooFinanceAnalysis
from isthisstockgood.Active.Zacks import Zacks
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
        monkeypatch.setenv("ISG_MSN_MONEY_API_KEY", "test-key")

        def fake_fetch_msn_money_data(self: DataFetcher) -> None:
            self.msn_money = MSNMoney(self.ticker_symbol)
            autocomplete_payload = test_data_manager.load_text("msn_autocomplete.json")
            self.msn_money.extract_stock_id(autocomplete_payload)
            self.msn_money.parse_annual_report_data(test_data_manager.load_text("msn_annual_statements.json"))
            self.msn_money.parse_ratios_data(test_data_manager.load_text("msn_key_ratios.json"))
            self.msn_money.parse_quotes_data(test_data_manager.load_text("msn_quotes.json"))
            if not self.msn_money.description:
                self.msn_money.description = "Test company description"

        def fake_fetch_yahoo_finance_analysis(self: DataFetcher) -> None:
            self.yahoo_finance_analysis = YahooFinanceAnalysis(self.ticker_symbol)
            self.yahoo_finance_analysis.parse_analyst_five_year_growth_rate(
                test_data_manager.load_text("yahoo_analysis.html")
            )

        def fake_fetch_zacks_analysis(self: DataFetcher) -> None:
            self.zacks_analysis = Zacks(self.ticker_symbol)
            response = SimpleNamespace(status_code=200, text=test_data_manager.load_text("zacks_analysis.html"))
            self.zacks_analysis.parse(response)

        monkeypatch.setattr(DataFetcher, "fetch_msn_money_data", fake_fetch_msn_money_data)
        monkeypatch.setattr(DataFetcher, "fetch_yahoo_finance_analysis", fake_fetch_yahoo_finance_analysis)
        monkeypatch.setattr(DataFetcher, "fetch_zacks_analysis", fake_fetch_zacks_analysis)

    return _apply
