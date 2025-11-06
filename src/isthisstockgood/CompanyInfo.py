from dataclasses import dataclass
from typing import List


@dataclass
class CompanyInfo:
    ticker_symbol: str
    name: str
    description: str
    industry: str
    current_price: float
    average_volume: float
    market_cap: float
    shares_outstanding: int
    pe_high: float
    pe_low: float
    roic: float
    roic_averages: List[float]
    equity: float
    equity_growth_rates: List[float]
    free_cash_flow: float
    free_cash_flow_growth_rates: List[float]
    revenue: float
    revenue_growth_rates: List[float]
    eps: float
    quarterly_eps: List[float]
    eps_growth_rates: List[float]
    debt_equity_ratio: float
    last_year_net_income: float
    total_debt: float
