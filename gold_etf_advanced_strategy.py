"""
黄金ETF联接基金量化策略（进阶版）
包含：择时策略、定投增强策略、多基金对比分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# 1. 数据加载
# ============================================================

def load_all_funds(filepath: str) -> dict[str, pd.DataFrame]:
    """加载所有基金数据"""
    df = pd.read_csv(filepath)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    funds = {
        "华安黄金": "华安黄金ETF联接C(000217)_单位净值",
        "国泰黄金": "国泰黄金ETF联接C(004253)_单位净值",
        "博时黄金": "博时黄金ETF联接C(002611)_单位净值",
        "易方达黄金": "易方达黄金ETF联接C(002963)_单位净值",
    }

    result = {}
    for name, col in funds.items():
        fund_df = df[["日期"]].copy()
        fund_df["nav"] = df[col].astype(float)
        fund_df["daily_return"] = fund_df["nav"].pct_change()
        result[name] = fund_df

    return result


# ============================================================
# 2. 技术指标
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """添加所有技术指标"""
    # 均线
    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df["nav"].rolling(p).mean()

    # RSI
    delta = df["nav"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta).where(delta < 0, 0).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + gain / loss))

    # MACD
    ema12 = df["nav"].ewm(span=12).mean()
    ema26 = df["nav"].ewm(span=26).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    # 布林带
    df["BB_MID"] = df["nav"].rolling(20).mean()
    bb_std = df["nav"].rolling(20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * bb_std
    df["BB_LOWER"] = df["BB_MID"] - 2 * bb_std

    # 回撤
    df["cummax"] = df["nav"].cummax()
    df["drawdown"] = (df["nav"] - df["cummax"]) / df["cummax"]

    # 波动率（20日）
    df["volatility"] = df["daily_return"].rolling(20).std() * np.sqrt(252)

    return df


# ============================================================
# 3. 策略1：多因子择时策略
# ============================================================

def timing_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """多因子择时策略"""
    df = df.copy()
    df["signal"] = 0

    # 买入条件计分
    buy_score = pd.Series(0, index=df.index)
    buy_score += (df["MA5"] > df["MA20"]).astype(int)  # 均线多头
    buy_score += (df["RSI"] < 35).astype(int)  # RSI超卖
    buy_score += (df["nav"] < df["BB_LOWER"]).astype(int)  # 触及布林下轨
    buy_score += (df["DIF"] > df["DEA"]).astype(int)  # MACD金叉
    buy_score += (df["nav"] > df["MA20"]).astype(int)  # 站上MA20

    # 卖出条件计分
    sell_score = pd.Series(0, index=df.index)
    sell_score += (df["MA5"] < df["MA20"]).astype(int)  # 均线空头
    sell_score += (df["RSI"] > 70).astype(int)  # RSI超买
    sell_score += (df["nav"] > df["BB_UPPER"]).astype(int)  # 触及布林上轨
    sell_score += (df["DIF"] < df["DEA"]).astype(int)  # MACD死叉

    # 信号生成
    df.loc[buy_score >= 3, "signal"] = 1
    df.loc[sell_score >= 3, "signal"] = -1
    df.loc[df["drawdown"] < -0.08, "signal"] = -1  # 止损8%

    df["buy_score"] = buy_score
    df["sell_score"] = sell_score

    return df


# ============================================================
# 4. 策略2：定投增强策略
# ============================================================

def dca_enhanced_strategy(df: pd.DataFrame, base_amount: float = 1000) -> pd.DataFrame:
    """
    定投增强策略
    - 普通定投：每周固定金额
    - 增强：RSI低时多投，高时少投
    """
    df = df.copy()
    df["dca_amount"] = 0.0
    df["dca_shares"] = 0.0
    df["total_invested"] = 0.0
    df["total_shares"] = 0.0

    total_invested = 0
    total_shares = 0

    # 每周定投（每5个交易日）
    for i in range(0, len(df), 5):
        row = df.iloc[i]
        rsi = row["RSI"]

        # 根据RSI调整定投金额
        if pd.isna(rsi):
            amount = base_amount
        elif rsi < 30:
            amount = base_amount * 2.0  # 超卖，双倍定投
        elif rsi < 40:
            amount = base_amount * 1.5
        elif rsi < 50:
            amount = base_amount * 1.0
        elif rsi < 60:
            amount = base_amount * 0.8
        elif rsi < 70:
            amount = base_amount * 0.5
        else:
            amount = base_amount * 0.3  # 超买，减少定投

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
# 5. 回测引擎
# ============================================================

def backtest(df: pd.DataFrame, initial_capital: float = 100000, commission: float = 0.001) -> pd.DataFrame:
    """执行择时策略回测"""
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
                trades.append({"date": row["日期"], "action": "BUY", "price": nav, "shares": shares})

        elif signal == -1 and position > 0:
            revenue = position * nav * (1 - commission)
            capital += revenue
            trades.append({"date": row["日期"], "action": "SELL", "price": nav, "shares": position})
            position = 0

        total_value.append(capital + position * nav)

    df["total_value"] = total_value
    df["strategy_return"] = df["total_value"].pct_change()

    return df, pd.DataFrame(trades) if trades else pd.DataFrame()


# ============================================================
# 6. 绩效评估
# ============================================================

def evaluate(df: pd.DataFrame, trades: pd.DataFrame, initial_capital: float = 100000) -> dict:
    """评估策略绩效"""
    # 基准收益
    benchmark = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100

    # 策略收益
    strategy = (df["total_value"].iloc[-1] / initial_capital - 1) * 100

    # 年化收益
    days = (df["日期"].iloc[-1] - df["日期"].iloc[0]).days
    annual = ((1 + strategy / 100) ** (365 / days) - 1) * 100

    # 最大回撤
    cummax = df["total_value"].cummax()
    max_dd = ((df["total_value"] - cummax) / cummax).min() * 100

    # 夏普比率
    daily_ret = df["strategy_return"].dropna()
    if len(daily_ret) > 0 and daily_ret.std() > 0:
        sharpe = (daily_ret.mean() * 252 - 0.02) / (daily_ret.std() * np.sqrt(252))
    else:
        sharpe = 0

    # 胜率
    if not trades.empty and len(trades) >= 2:
        wins = 0
        pairs = min(len(trades[trades["action"] == "BUY"]), len(trades[trades["action"] == "SELL"]))
        buys = trades[trades["action"] == "BUY"]["price"].values[:pairs]
        sells = trades[trades["action"] == "SELL"]["price"].values[:pairs]
        win_rate = np.sum(sells > buys) / pairs * 100 if pairs > 0 else 0
    else:
        win_rate = 0

    return {
        "基准收益": f"{benchmark:.2f}%",
        "策略收益": f"{strategy:.2f}%",
        "年化收益": f"{annual:.2f}%",
        "最大回撤": f"{max_dd:.2f}%",
        "夏普比率": f"{sharpe:.2f}",
        "胜率": f"{win_rate:.1f}%",
        "交易次数": len(trades),
    }


# ============================================================
# 7. 主程序：多基金对比
# ============================================================

def main():
    filepath = r"c:\Users\FOH\Desktop\量化投资\fund_data\黄金ETF联接基金_半年数据.csv"

    print("=" * 70)
    print("黄金ETF联接基金量化策略分析（进阶版）")
    print("=" * 70)

    # 加载所有基金
    funds = load_all_funds(filepath)
    print(f"\n数据区间: 2025-11-24 ~ 2026-05-21 (约6个月)")

    # ============================================================
    # Part 1: 四只基金择时策略对比
    # ============================================================
    print("\n" + "=" * 70)
    print("Part 1: 择时策略对比（四只基金）")
    print("=" * 70)

    results = []
    for name, fund_df in funds.items():
        fund_df = add_indicators(fund_df)
        fund_df = timing_strategy(fund_df)
        fund_df, trades = backtest(fund_df)
        perf = evaluate(fund_df, trades)
        perf["基金"] = name
        results.append(perf)

    result_df = pd.DataFrame(results)
    result_df = result_df.set_index("基金")
    print(result_df.to_string())

    # ============================================================
    # Part 2: 定投增强策略
    # ============================================================
    print("\n" + "=" * 70)
    print("Part 2: 定投增强策略（以华安黄金为例）")
    print("=" * 70)

    huian = funds["华安黄金"].copy()
    huian = add_indicators(huian)
    huian = dca_enhanced_strategy(huian, base_amount=1000)

    # 普通定投收益
    total_invested = huian["total_invested"].iloc[-1]
    dca_value = huian["dca_value"].iloc[-1]
    dca_return = (dca_value / total_invested - 1) * 100

    print(f"\n定投周期: 每周一次（每5个交易日）")
    print(f"基础金额: 1000元/次")
    print(f"增强逻辑: RSI<30双倍投，RSI>70减半投")
    print(f"\n总投入: {total_invested:,.0f}元")
    print(f"当前市值: {dca_value:,.0f}元")
    print(f"定投收益: {dca_return:+.2f}%")

    # ============================================================
    # Part 3: 最新信号状态
    # ============================================================
    print("\n" + "=" * 70)
    print("Part 3: 最新信号状态")
    print("=" * 70)

    for name, fund_df in funds.items():
        fund_df = add_indicators(fund_df)
        last = fund_df.iloc[-1]
        print(f"\n{name}:")
        print(f"  净值: {last['nav']:.4f}")
        print(f"  RSI: {last['RSI']:.1f}")
        print(f"  MA5: {last['MA5']:.4f} | MA20: {last['MA20']:.4f}")
        print(f"  均线状态: {'多头' if last['MA5'] > last['MA20'] else '空头'}")
        print(f"  回撤: {last['drawdown']*100:.2f}%")

    # ============================================================
    # Part 4: 投资建议
    # ============================================================
    print("\n" + "=" * 70)
    print("Part 4: 策略建议")
    print("=" * 70)

    print("""
┌─────────────────────────────────────────────────────────────────┐
│                    黄金ETF量化策略总结                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【策略1: 择时交易】                                            │
│   • 买入: MA5>MA20 + RSI<35 + 触及布林下轨 (满足3个)            │
│   • 卖出: MA5<MA20 + RSI>70 + 触及布林上轨 (满足3个)            │
│   • 止损: 回撤超过8%强制离场                                    │
│   • 适合: 有一定技术分析基础的投资者                            │
│                                                                 │
│  【策略2: 定投增强】                                            │
│   • 基础: 每周定投1000元                                        │
│   • 增强: RSI<30时双倍投，RSI>70时减半投                        │
│   • 优势: 纪律性强，平滑成本，不需要择时                        │
│   • 适合: 普通投资者、上班族                                    │
│                                                                 │
│  【资产配置建议】                                               │
│   • 黄金占总资产: 10%-15%                                       │
│   • 建仓方式: 分3-6个月建仓，不一次性重仓                      │
│   • 持有周期: 建议1年以上                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    """)

    return funds, result_df


if __name__ == "__main__":
    funds, results = main()
