from pydantic import BaseModel
from typing import Optional


class FundInfo(BaseModel):
    code: str
    name: str
    fund_type: str = "其他"


class FundCreate(BaseModel):
    code: str
    name: str
    fund_type: str = "其他"


class FundUpdate(BaseModel):
    name: Optional[str] = None
    fund_type: Optional[str] = None


class NavData(BaseModel):
    code: str
    date: str
    nav: float
    cumulative_nav: Optional[float] = None
    daily_return: Optional[float] = None


class FundNavResponse(BaseModel):
    fund: FundInfo
    data: list[NavData]
    latest_nav: Optional[float] = None
    half_year_return: Optional[float] = None


class StrategyRequest(BaseModel):
    strategy_name: str
    fund_code: str
    initial_capital: float = 100000
    commission: float = 0.001


class PerformanceResult(BaseModel):
    benchmark_return: float
    strategy_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    trade_count: int


class TradeRecord(BaseModel):
    date: str
    action: str
    price: float
    shares: Optional[float] = None
    amount: Optional[float] = None


class BacktestResponse(BaseModel):
    strategy_name: str
    fund_code: str
    perf: PerformanceResult
    trades: list[TradeRecord]
    dates: list[str]
    equity_curve: list[float]
    nav: list[float]


class SignalData(BaseModel):
    code: str
    name: str
    nav: float
    rsi6: Optional[float] = None
    rsi14: Optional[float] = None
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    trend: str = "未知"
    drawdown: float = 0
    momentum: Optional[float] = None


class StrategyInfo(BaseModel):
    name: str
    description: str
