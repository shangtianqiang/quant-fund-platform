"""
运行所有策略回测，输出JSON供看板使用
"""
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, r"c:\Users\FOH\Desktop\量化投资")

base_path = r"c:\Users\FOH\Desktop\量化投资\fund_data"
csv_path = f"{base_path}/黄金ETF联接基金_半年数据.csv"

# ============================================================
# 技术指标（合并三个策略文件的指标）
# ============================================================

def add_indicators(df):
    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df["nav"].rolling(p).mean()

    for p in [6, 14]:
        delta = df["nav"].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta).where(delta < 0, 0).rolling(p).mean()
        df[f"RSI{p}"] = 100 - (100 / (1 + gain / loss))
    df["RSI"] = df["RSI14"]

    ema12 = df["nav"].ewm(span=12).mean()
    ema26 = df["nav"].ewm(span=26).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    df["BB_MID"] = df["nav"].rolling(20).mean()
    bb_std = df["nav"].rolling(20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * bb_std
    df["BB_LOWER"] = df["BB_MID"] - 2 * bb_std

    df["cummax"] = df["nav"].cummax()
    df["drawdown"] = (df["nav"] - df["cummax"]) / df["cummax"]
    df["trend"] = np.where(df["MA20"] > df["MA60"], 1, -1)
    df["momentum"] = df["nav"] / df["nav"].shift(20) - 1
    df["volatility"] = df["daily_return"].rolling(20).std() * np.sqrt(252)

    return df


# ============================================================
# 策略定义
# ============================================================

def strategy_multi_factor(df):
    """多因子择时"""
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


def strategy_trend_following(df):
    """趋势跟踪"""
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


def strategy_grid(df, grid_size=0.03):
    """网格交易"""
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


def strategy_dca_enhanced(df, base_amount=1000):
    """定投增强"""
    df = df.copy()
    df["dca_amount"] = 0.0
    df["dca_shares"] = 0.0
    total_invested = 0
    total_shares = 0

    for i in range(0, len(df), 5):
        row = df.iloc[i]
        rsi = row["RSI14"]
        trend = row["trend"]
        dd = row["drawdown"]

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


# ============================================================
# 回测引擎
# ============================================================

def backtest(df, initial_capital=100000, commission=0.001):
    capital = initial_capital
    position = 0
    total_value = []
    trades = []

    for _, row in df.iterrows():
        nav = row["nav"]
        signal = row["signal"]
        if signal == 1 and position == 0:
            shares = capital / (nav * (1 + commission))
            cost = shares * nav * (1 + commission)
            if cost <= capital:
                position = shares
                capital -= cost
                trades.append({"date": str(row["日期"])[:10], "action": "BUY", "price": round(nav, 4)})
        elif signal == -1 and position > 0:
            revenue = position * nav * (1 - commission)
            capital += revenue
            trades.append({"date": str(row["日期"])[:10], "action": "SELL", "price": round(nav, 4)})
            position = 0
        total_value.append(capital + position * nav)

    df["total_value"] = total_value
    df["strategy_return"] = df["total_value"].pct_change()
    return df, trades


def calc_perf(df, trades, initial_capital=100000):
    benchmark = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100
    strategy = (df["total_value"].iloc[-1] / initial_capital - 1) * 100
    days = (df["日期"].iloc[-1] - df["日期"].iloc[0]).days
    annual = ((1 + strategy / 100) ** (365 / days) - 1) * 100 if days > 0 else 0

    cummax = df["total_value"].cummax()
    max_dd = ((df["total_value"] - cummax) / cummax).min() * 100

    daily_ret = df["strategy_return"].dropna()
    sharpe = (daily_ret.mean() * 252 - 0.02) / (daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 0 and daily_ret.std() > 0 else 0

    buys = [t["price"] for t in trades if t["action"] == "BUY"]
    sells = [t["price"] for t in trades if t["action"] == "SELL"]
    pairs = min(len(buys), len(sells))
    win_rate = sum(s > b for s, b in zip(sells[:pairs], buys[:pairs])) / pairs * 100 if pairs > 0 else 0

    return {
        "benchmark": round(benchmark, 2),
        "strategy": round(strategy, 2),
        "annual": round(annual, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1),
        "trade_count": len(trades),
    }


# ============================================================
# 主程序
# ============================================================

def main():
    df = pd.read_csv(csv_path)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    fund_cols = {
        "华安黄金": "华安黄金ETF联接C(000217)_单位净值",
        "国泰黄金": "国泰黄金ETF联接C(004253)_单位净值",
        "博时黄金": "博时黄金ETF联接C(002611)_单位净值",
        "易方达黄金": "易方达黄金ETF联接C(002963)_单位净值",
    }

    strategies = {
        "多因子择时": strategy_multi_factor,
        "趋势跟踪": strategy_trend_following,
        "网格交易": strategy_grid,
    }

    output = {
        "dates": [str(d)[:10] for d in df["日期"]],
        "funds": {},
        "strategies": {},
        "dca": {},
        "latest_signals": {},
    }

    # 基金净值数据
    for name, col in fund_cols.items():
        nav_series = df[col].astype(float).tolist()
        gr_series = df[col].astype(float).pct_change().tolist()
        output["funds"][name] = {
            "nav": [round(v, 4) if not pd.isna(v) else None for v in nav_series],
            "growth": [round(v * 100, 2) if not pd.isna(v) else None for v in gr_series],
        }

    # 各策略回测（以华安黄金为主标的）
    for sname, sfunc in strategies.items():
        fund_df = pd.DataFrame({"日期": df["日期"], "nav": df[fund_cols["华安黄金"]].astype(float)})
        fund_df["daily_return"] = fund_df["nav"].pct_change()
        fund_df = add_indicators(fund_df)
        fund_df = sfunc(fund_df)
        fund_df, trades = backtest(fund_df)
        perf = calc_perf(fund_df, trades)

        output["strategies"][sname] = {
            "perf": perf,
            "trades": trades,
            "equity_curve": [round(v, 2) for v in fund_df["total_value"].tolist()],
            "nav": [round(v, 4) for v in fund_df["nav"].tolist()],
        }

    # 定投增强策略
    fund_df = pd.DataFrame({"日期": df["日期"], "nav": df[fund_cols["华安黄金"]].astype(float)})
    fund_df["daily_return"] = fund_df["nav"].pct_change()
    fund_df = add_indicators(fund_df)
    fund_df = strategy_dca_enhanced(fund_df)
    total_invested = fund_df["total_invested"].iloc[-1]
    dca_value = fund_df["dca_value"].iloc[-1]
    dca_return = (dca_value / total_invested - 1) * 100 if total_invested > 0 else 0

    output["dca"] = {
        "total_invested": round(total_invested, 2),
        "dca_value": round(dca_value, 2),
        "dca_return": round(dca_return, 2),
        "invest_curve": [round(v, 2) if not pd.isna(v) else 0 for v in fund_df["total_invested"].tolist()],
        "value_curve": [round(v, 2) if not pd.isna(v) else 0 for v in fund_df["dca_value"].tolist()],
    }

    # 最新信号状态
    for name, col in fund_cols.items():
        fund_df = pd.DataFrame({"日期": df["日期"], "nav": df[col].astype(float)})
        fund_df["daily_return"] = fund_df["nav"].pct_change()
        fund_df = add_indicators(fund_df)
        last = fund_df.iloc[-1]
        output["latest_signals"][name] = {
            "nav": round(last["nav"], 4),
            "rsi6": round(last["RSI6"], 1) if not pd.isna(last["RSI6"]) else None,
            "rsi14": round(last["RSI14"], 1) if not pd.isna(last["RSI14"]) else None,
            "ma5": round(last["MA5"], 4) if not pd.isna(last["MA5"]) else None,
            "ma20": round(last["MA20"], 4) if not pd.isna(last["MA20"]) else None,
            "ma60": round(last["MA60"], 4) if not pd.isna(last["MA60"]) else None,
            "trend": "上升" if last["trend"] == 1 else "下降",
            "drawdown": round(last["drawdown"] * 100, 2),
            "momentum": round(last["momentum"] * 100, 2) if not pd.isna(last["momentum"]) else None,
        }

    # 保存
    out_path = f"{base_path}/strategy_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"策略数据已保存: {out_path}")


if __name__ == "__main__":
    main()
