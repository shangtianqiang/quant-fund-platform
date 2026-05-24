import pandas as pd
import numpy as np


def backtest(df: pd.DataFrame, initial_capital: float = 100000, commission: float = 0.001):
    capital = initial_capital
    position = 0
    total_value = []
    trades = []

    for _, row in df.iterrows():
        nav = row["nav"]
        signal = row.get("signal", 0)

        if signal == 1 and position == 0:
            shares = capital / (nav * (1 + commission))
            cost = shares * nav * (1 + commission)
            if cost <= capital:
                position = shares
                capital -= cost
                trades.append({
                    "date": str(row["date"])[:10],
                    "action": "BUY",
                    "price": round(nav, 4),
                    "shares": round(shares, 2),
                    "amount": round(cost, 2),
                })

        elif signal == -1 and position > 0:
            revenue = position * nav * (1 - commission)
            capital += revenue
            trades.append({
                "date": str(row["date"])[:10],
                "action": "SELL",
                "price": round(nav, 4),
                "shares": round(position, 2),
                "amount": round(revenue, 2),
            })
            position = 0

        total_value.append(capital + position * nav)

    df = df.copy()
    df["total_value"] = total_value
    df["strategy_return"] = df["total_value"].pct_change()
    return df, trades


def calc_performance(df: pd.DataFrame, trades: list, initial_capital: float = 100000) -> dict:
    benchmark = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100
    strategy = (df["total_value"].iloc[-1] / initial_capital - 1) * 100

    days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    annual = ((1 + strategy / 100) ** (365 / days) - 1) * 100 if days > 0 else 0

    cummax = df["total_value"].cummax()
    max_dd = ((df["total_value"] - cummax) / cummax).min() * 100

    daily_ret = df["strategy_return"].dropna()
    sharpe = 0
    if len(daily_ret) > 0 and daily_ret.std() > 0:
        sharpe = (daily_ret.mean() * 252 - 0.02) / (daily_ret.std() * np.sqrt(252))

    buys = [t["price"] for t in trades if t["action"] == "BUY"]
    sells = [t["price"] for t in trades if t["action"] == "SELL"]
    pairs = min(len(buys), len(sells))
    win_rate = sum(s > b for s, b in zip(sells[:pairs], buys[:pairs])) / pairs * 100 if pairs > 0 else 0

    return {
        "benchmark_return": round(benchmark, 2),
        "strategy_return": round(strategy, 2),
        "annual_return": round(annual, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "win_rate": round(win_rate, 1),
        "trade_count": len(trades),
    }
