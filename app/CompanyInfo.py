from dataclasses import dataclass
from typing import List


@dataclass
class CompanyInfo:
    tickersymbol: str
    name: str = None
    description: str = None
    industry: str = None
    currentprice: float = 0.0
    averagevolume: int = 0
    marketcap: int = 0
    sharesoutstanding: int = 0
    pehigh: float = 0.0
    pelow: float = 0.0
    roic: float = 0.0
    roicaverages: List[float] = None
    equity: float = 0.0
    equitygrowthrates: List[float] = None
    freecashflow: float = 0.0
    freecashflowgrowthrates: List[float] = None
    revenue: float = 0.0
    revenuegrowthrates: List[float] = None
    eps: float = 0.0
    quarterlyeps: List[float] = None
    epsgrowthrates: List[float] = None
    debtequityratio: float = 0.0
    lastyearnetincome: float = 0.0
    totaldebt: float = 0.0
