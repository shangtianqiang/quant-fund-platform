import pandas as pd
import numpy as np


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    nav_col = "nav"

    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df[nav_col].rolling(p).mean()

    for p in [6, 14]:
        delta = df[nav_col].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta).where(delta < 0, 0).rolling(p).mean()
        df[f"RSI{p}"] = 100 - (100 / (1 + gain / loss))
    df["RSI"] = df["RSI14"]

    ema12 = df[nav_col].ewm(span=12).mean()
    ema26 = df[nav_col].ewm(span=26).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    df["BB_MID"] = df[nav_col].rolling(20).mean()
    bb_std = df[nav_col].rolling(20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * bb_std
    df["BB_LOWER"] = df["BB_MID"] - 2 * bb_std

    df["cummax"] = df[nav_col].cummax()
    df["drawdown"] = (df[nav_col] - df["cummax"]) / df["cummax"]
    df["trend"] = np.where(df["MA20"] > df["MA60"], 1, -1)
    df["momentum"] = df[nav_col] / df[nav_col].shift(20) - 1

    if "daily_return" not in df.columns:
        df["daily_return"] = df[nav_col].pct_change()
    df["volatility"] = df["daily_return"].rolling(20).std() * np.sqrt(252)

    return df
