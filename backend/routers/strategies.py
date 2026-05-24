from fastapi import APIRouter, HTTPException
from models import StrategyRequest, StrategyInfo, BacktestResponse
from services.strategy_engine import STRATEGIES
from services.indicator_engine import add_indicators
from services.backtester import backtest, calc_performance
from services.data_fetcher import load_fund_data_to_df
from database import get_db
import json

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyInfo])
def list_strategies():
    return [
        StrategyInfo(name=name, description=info["description"])
        for name, info in STRATEGIES.items()
    ]


@router.post("/run")
def run_strategy(req: StrategyRequest):
    if req.strategy_name not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"未知策略: {req.strategy_name}")

    df = load_fund_data_to_df(req.fund_code)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"基金 {req.fund_code} 无数据")

    df["daily_return"] = df["nav"].pct_change()
    df = add_indicators(df)

    strategy_func = STRATEGIES[req.strategy_name]["func"]
    df = strategy_func(df)

    if req.strategy_name == "定投增强":
        total_invested = df["total_invested"].iloc[-1]
        dca_value = df["dca_value"].iloc[-1]
        dca_return = round((dca_value / total_invested - 1) * 100, 2) if total_invested > 0 else 0
        return {
            "strategy_name": req.strategy_name,
            "fund_code": req.fund_code,
            "type": "dca",
            "perf": {
                "total_invested": round(total_invested, 2),
                "dca_value": round(dca_value, 2),
                "dca_return": dca_return,
            },
            "dates": [str(d)[:10] for d in df["date"]],
            "invest_curve": [round(v, 2) if not (v != v) else 0 for v in df["total_invested"].tolist()],
            "value_curve": [round(v, 2) if not (v != v) else 0 for v in df["dca_value"].tolist()],
            "nav": [round(v, 4) for v in df["nav"].tolist()],
            "trades": [],
        }

    df_bt, trades = backtest(df, req.initial_capital, req.commission)
    perf = calc_performance(df_bt, trades, req.initial_capital)

    # 保存到数据库
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO backtest_results
               (strategy_name, fund_code, initial_capital, benchmark_return, strategy_return,
                annual_return, max_drawdown, sharpe_ratio, win_rate, trade_count, equity_curve)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (req.strategy_name, req.fund_code, req.initial_capital,
             perf["benchmark_return"], perf["strategy_return"], perf["annual_return"],
             perf["max_drawdown"], perf["sharpe_ratio"], perf["win_rate"], perf["trade_count"],
             json.dumps([round(v, 2) for v in df_bt["total_value"].tolist()]))
        )
        backtest_id = cursor.lastrowid
        for t in trades:
            conn.execute(
                "INSERT INTO trades (backtest_id, date, action, price, shares, amount) VALUES (?, ?, ?, ?, ?, ?)",
                (backtest_id, t["date"], t["action"], t["price"], t.get("shares"), t.get("amount"))
            )

    return {
        "strategy_name": req.strategy_name,
        "fund_code": req.fund_code,
        "type": "timing",
        "perf": perf,
        "dates": [str(d)[:10] for d in df_bt["date"]],
        "equity_curve": [round(v, 2) for v in df_bt["total_value"].tolist()],
        "nav": [round(v, 4) for v in df_bt["nav"].tolist()],
        "trades": trades,
    }


@router.get("/results")
def get_results(limit: int = 10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM backtest_results ORDER BY run_date DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
