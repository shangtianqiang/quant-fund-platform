import pandas as pd
import numpy as np


def strategy_multi_factor(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = 0

    buy_score = pd.Series(0, index=df.index)
    buy_score += (df["MA5"] > df["MA20"]).astype(int)
    buy_score += (df["RSI"] < 35).astype(int)
    buy_score += (df["nav"] < df["BB_LOWER"]).astype(int)
    buy_score += (df["DIF"] > df["DEA"]).astype(int)
    buy_score += (df["nav"] > df["MA20"]).astype(int)

    sell_score = pd.Series(0, index=df.index)
    sell_score += (df["MA5"] < df["MA20"]).astype(int)
    sell_score += (df["RSI"] > 70).astype(int)
    sell_score += (df["nav"] > df["BB_UPPER"]).astype(int)
    sell_score += (df["DIF"] < df["DEA"]).astype(int)

    df.loc[buy_score >= 3, "signal"] = 1
    df.loc[sell_score >= 3, "signal"] = -1
    df.loc[df["drawdown"] < -0.08, "signal"] = -1
    return df


def strategy_trend_following(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = 0
    uptrend = df["trend"] == 1
    downtrend = df["trend"] == -1

    buy_cond1 = uptrend & (df["RSI14"] < 40) & (df["nav"] > df["MA20"])
    buy_cond2 = (df["RSI14"] < 25) & (df["drawdown"] < -0.15)
    buy_cond3 = (df["DIF"] > df["DEA"]) & (df["DIF"].shift(1) <= df["DEA"].shift(1)) & (df["momentum"] > 0)

    sell_cond1 = downtrend & (df["RSI14"] > 60)
    sell_cond2 = (df["RSI14"] > 75)
    sell_cond3 = (df["drawdown"] < -0.08)
    sell_cond4 = (df["DIF"] < df["DEA"]) & (df["DIF"].shift(1) >= df["DEA"].shift(1)) & (df["momentum"] < 0)

    df.loc[buy_cond1 | buy_cond2 | buy_cond3, "signal"] = 1
    df.loc[sell_cond1 | sell_cond2 | sell_cond3 | sell_cond4, "signal"] = -1
    return df


def strategy_grid(df: pd.DataFrame, grid_size: float = 0.03) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = 0
    position = 0
    last_price = df["nav"].iloc[0]

    for i in range(1, len(df)):
        price = df.iloc[i]["nav"]
        change = (price - last_price) / last_price
        if change <= -grid_size and position < 3:
            df.iloc[i, df.columns.get_loc("signal")] = 1
            position += 1
            last_price = price
        elif change >= grid_size and position > 0:
            df.iloc[i, df.columns.get_loc("signal")] = -1
            position -= 1
            last_price = price
    return df


def strategy_dca_enhanced(df: pd.DataFrame, base_amount: float = 1000) -> pd.DataFrame:
    df = df.copy()
    df["dca_amount"] = 0.0
    df["dca_shares"] = 0.0
    total_invested = 0
    total_shares = 0

    for i in range(0, len(df), 5):
        row = df.iloc[i]
        rsi = row.get("RSI14", 50)
        trend = row.get("trend", 1)
        dd = row.get("drawdown", 0)

        m = 1.0
        if not pd.isna(rsi):
            if rsi < 25: m *= 2.5
            elif rsi < 35: m *= 2.0
            elif rsi < 45: m *= 1.5
            elif rsi < 55: m *= 1.0
            elif rsi < 65: m *= 0.7
            elif rsi < 75: m *= 0.5
            else: m *= 0.3

        if trend == 1: m *= 1.2
        else: m *= 0.8

        if not pd.isna(dd):
            if dd < -0.20: m *= 2.0
            elif dd < -0.15: m *= 1.5
            elif dd < -0.10: m *= 1.2

        amount = base_amount * m
        shares = amount / row["nav"]
        total_invested += amount
        total_shares += shares
        df.iloc[i, df.columns.get_loc("dca_amount")] = amount
        df.iloc[i, df.columns.get_loc("dca_shares")] = shares

    df["total_invested"] = df["dca_amount"].cumsum()
    df["total_shares"] = df["dca_shares"].cumsum()
    df["dca_value"] = df["total_shares"] * df["nav"]
    df["dca_return"] = (df["dca_value"] / df["total_invested"] - 1) * 100
    return df


STRATEGIES = {
    "多因子择时": {
        "func": strategy_multi_factor,
        "description": "综合MA、RSI、MACD、布林带多因子择时，满足3个以上条件触发交易，8%止损",
    },
    "趋势跟踪": {
        "func": strategy_trend_following,
        "description": "趋势感知策略，上升趋势积极买入，下降趋势谨慎操作",
    },
    "网格交易": {
        "func": strategy_grid,
        "description": "每跌3%加仓一次，每涨3%减仓一次，适合震荡行情",
    },
    "定投增强": {
        "func": strategy_dca_enhanced,
        "description": "每周定投，RSI低多投、RSI高少投，趋势+回撤调整",
    },
}
