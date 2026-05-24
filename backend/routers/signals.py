from fastapi import APIRouter, HTTPException
from services.data_fetcher import get_all_funds, load_fund_data_to_df
from services.indicator_engine import add_indicators
from models import SignalData

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("", response_model=list[SignalData])
def get_all_signals():
    funds = get_all_funds()
    signals = []
    for fund in funds:
        try:
            signal = _calc_signal(fund["code"], fund["name"])
            signals.append(signal)
        except Exception:
            signals.append(SignalData(
                code=fund["code"], name=fund["name"], nav=0,
                trend="无数据"
            ))
    return signals


@router.get("/{code}", response_model=SignalData)
def get_signal(code: str):
    funds = get_all_funds()
    fund = next((f for f in funds if f["code"] == code), None)
    if not fund:
        raise HTTPException(status_code=404, detail=f"基金 {code} 不存在")
    return _calc_signal(code, fund["name"])


def _calc_signal(code: str, name: str) -> SignalData:
    df = load_fund_data_to_df(code)
    if df.empty:
        return SignalData(code=code, name=name, nav=0, trend="无数据")

    df["daily_return"] = df["nav"].pct_change()
    df = add_indicators(df)
    last = df.iloc[-1]

    def safe_val(col):
        v = last.get(col)
        return round(float(v), 2) if v is not None and not (v != v) else None

    return SignalData(
        code=code,
        name=name,
        nav=round(float(last["nav"]), 4),
        rsi6=safe_val("RSI6"),
        rsi14=safe_val("RSI14"),
        ma5=safe_val("MA5"),
        ma20=safe_val("MA20"),
        ma60=safe_val("MA60"),
        trend="上升" if last.get("trend") == 1 else "下降",
        drawdown=round(float(last.get("drawdown", 0)) * 100, 2),
        momentum=safe_val("momentum"),
    )
