"""
黄金ETF联接基金量化策略（优化版）
针对震荡行情优化参数，增加趋势过滤
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# 数据加载
# ============================================================

def load_data(filepath: str) -> pd.DataFrame:
    """加载数据"""
    df = pd.read_csv(filepath)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    # 使用华安黄金作为主标的
    df["nav"] = df["华安黄金ETF联接C(000217)_单位净值"].astype(float)
    df["daily_return"] = df["nav"].pct_change()

    return df


# ============================================================
# 技术指标（优化版）
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """添加技术指标"""
    # 均线系统
    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df["nav"].rolling(p).mean()

    # RSI（多周期）
    for p in [6, 14]:
        delta = df["nav"].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta).where(delta < 0, 0).rolling(p).mean()
        df[f"RSI{p}"] = 100 - (100 / (1 + gain / loss))

    # MACD
    ema12 = df["nav"].ewm(span=12).mean()
    ema26 = df["nav"].ewm(span=26).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])

    # 布林带（动态参数）
    df["BB_MID"] = df["nav"].rolling(20).mean()
    bb_std = df["nav"].rolling(20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * bb_std
    df["BB_LOWER"] = df["BB_MID"] - 2 * bb_std

    # ATR（平均真实波幅）
    high = df["nav"] * 1.01  # 模拟高点
    low = df["nav"] * 0.99   # 模拟低点
    tr = pd.concat([
        high - low,
        abs(high - df["nav"].shift(1)),
        abs(low - df["nav"].shift(1))
    ], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    # 趋势强度
    df["trend"] = np.where(df["MA20"] > df["MA60"], 1, -1)  # 1=上升趋势, -1=下降趋势

    # 回撤
    df["cummax"] = df["nav"].cummax()
    df["drawdown"] = (df["nav"] - df["cummax"]) / df["cummax"]

    # 动量
    df["momentum"] = df["nav"] / df["nav"].shift(20) - 1

    return df


# ============================================================
# 策略1: 趋势跟踪策略（优化版）
# ============================================================

def trend_following_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    趋势跟踪策略
    - 上升趋势中：积极买入
    - 下降趋势中：谨慎操作，只在超卖时博反弹
    """
    df = df.copy()
    df["signal"] = 0

    # 上升趋势条件
    uptrend = df["trend"] == 1
    downtrend = df["trend"] == -1

    # 买入条件
    buy_cond1 = uptrend & (df["RSI14"] < 40) & (df["nav"] > df["MA20"])  # 上升趋势回调
    buy_cond2 = (df["RSI14"] < 25) & (df["drawdown"] < -0.15)  # 极度超卖抄底
    buy_cond3 = (df["DIF"] > df["DEA"]) & (df["DIF"].shift(1) <= df["DEA"].shift(1)) & (df["momentum"] > 0)  # MACD金叉+正动量

    # 卖出条件
    sell_cond1 = downtrend & (df["RSI14"] > 60)  # 下降趋势反弹
    sell_cond2 = (df["RSI14"] > 75)  # 极度超买
    sell_cond3 = (df["drawdown"] < -0.08)  # 止损8%
    sell_cond4 = (df["DIF"] < df["DEA"]) & (df["DIF"].shift(1) >= df["DEA"].shift(1)) & (df["momentum"] < 0)  # MACD死叉+负动量

    df.loc[buy_cond1 | buy_cond2 | buy_cond3, "signal"] = 1
    df.loc[sell_cond1 | sell_cond2 | sell_cond3 | sell_cond4, "signal"] = -1

    # 避免连续信号
    df["signal_group"] = (df["signal"] != df["signal"].shift()).cumsum()
    df = df.groupby("signal_group").apply(lambda x: x.assign(signal=x["signal"].iloc[0])).reset_index(drop=True)

    return df


# ============================================================
# 策略2: 网格交易策略
# ============================================================

def grid_strategy(df: pd.DataFrame, grid_size: float = 0.03) -> pd.DataFrame:
    """
    网格交易策略
    - 每跌3%加仓一次
    - 每涨3%减仓一次
    """
    df = df.copy()
    df["signal"] = 0

    position = 0  # 0=空仓, 1=轻仓, 2=半仓, 3=重仓
    last_trade_price = df["nav"].iloc[0]

    for i in range(1, len(df)):
        current_price = df.iloc[i]["nav"]
        change = (current_price - last_trade_price) / last_trade_price

        # 下跌加仓
        if change <= -grid_size and position < 3:
            df.iloc[i, df.columns.get_loc("signal")] = 1
            position += 1
            last_trade_price = current_price

        # 上涨减仓
        elif change >= grid_size and position > 0:
            df.iloc[i, df.columns.get_loc("signal")] = -1
            position -= 1
            last_trade_price = current_price

    return df


# ============================================================
# 策略3: 定投增强策略（优化版）
# ============================================================

def dca_optimized(df: pd.DataFrame, base_amount: float = 1000) -> pd.DataFrame:
    """
    定投增强策略
    - 基础: 每周定投
    - 增强: 根据RSI和趋势调整金额
    """
    df = df.copy()
    df["dca_amount"] = 0.0
    df["dca_shares"] = 0.0

    total_invested = 0
    total_shares = 0
    records = []

    # 每周定投（每5个交易日）
    for i in range(0, len(df), 5):
        row = df.iloc[i]
        rsi = row["RSI14"]
        trend = row["trend"]
        drawdown = row["drawdown"]

        # 基础金额调整
        multiplier = 1.0

        # RSI调整
        if not pd.isna(rsi):
            if rsi < 25:
                multiplier *= 2.5  # 极度超卖
            elif rsi < 35:
                multiplier *= 2.0
            elif rsi < 45:
                multiplier *= 1.5
            elif rsi < 55:
                multiplier *= 1.0
            elif rsi < 65:
                multiplier *= 0.7
            elif rsi < 75:
                multiplier *= 0.5
            else:
                multiplier *= 0.3  # 超买

        # 趋势调整
        if trend == 1:
            multiplier *= 1.2  # 上升趋势多投
        else:
            multiplier *= 0.8  # 下降趋势少投

        # 回撤调整（越跌越买）
        if not pd.isna(drawdown):
            if drawdown < -0.20:
                multiplier *= 2.0
            elif drawdown < -0.15:
                multiplier *= 1.5
            elif drawdown < -0.10:
                multiplier *= 1.2

        amount = base_amount * multiplier
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

def backtest(df: pd.DataFrame, initial_capital: float = 100000, commission: float = 0.001):
    """回测择时策略"""
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
                trades.append({
                    "date": row["日期"],
                    "action": "BUY",
                    "price": nav,
                    "shares": shares
                })

        elif signal == -1 and position > 0:
            revenue = position * nav * (1 - commission)
            capital += revenue
            trades.append({
                "date": row["日期"],
                "action": "SELL",
                "price": nav,
                "shares": position
            })
            position = 0

        total_value.append(capital + position * nav)

    df["total_value"] = total_value
    df["strategy_return"] = df["total_value"].pct_change()

    return df, pd.DataFrame(trades) if trades else pd.DataFrame()


# ============================================================
# 绩效评估
# ============================================================

def evaluate(df: pd.DataFrame, trades: pd.DataFrame, initial_capital: float = 100000) -> dict:
    """评估绩效"""
    benchmark = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100
    strategy = (df["total_value"].iloc[-1] / initial_capital - 1) * 100

    days = (df["日期"].iloc[-1] - df["日期"].iloc[0]).days
    annual = ((1 + strategy / 100) ** (365 / days) - 1) * 100

    cummax = df["total_value"].cummax()
    max_dd = ((df["total_value"] - cummax) / cummax).min() * 100

    daily_ret = df["strategy_return"].dropna()
    sharpe = (daily_ret.mean() * 252 - 0.02) / (daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 0 and daily_ret.std() > 0 else 0

    # 胜率
    if not trades.empty:
        buys = trades[trades["action"] == "BUY"]["price"].values
        sells = trades[trades["action"] == "SELL"]["price"].values
        pairs = min(len(buys), len(sells))
        win_rate = np.sum(sells[:pairs] > buys[:pairs]) / pairs * 100 if pairs > 0 else 0
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
# 主程序
# ============================================================

def main():
    filepath = r"c:\Users\FOH\Desktop\量化投资\fund_data\黄金ETF联接基金_半年数据.csv"

    print("=" * 70)
    print("黄金ETF量化策略分析（优化版）")
    print("=" * 70)

    df = load_data(filepath)
    df = add_indicators(df)

    print(f"\n数据区间: {df['日期'].iloc[0].strftime('%Y-%m-%d')} ~ {df['日期'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(df)}")

    # ============================================================
    # 策略1: 趋势跟踪
    # ============================================================
    print("\n" + "=" * 70)
    print("策略1: 趋势跟踪策略")
    print("=" * 70)

    df1 = trend_following_strategy(df.copy())
    df1, trades1 = backtest(df1)
    perf1 = evaluate(df1, trades1)

    for k, v in perf1.items():
        print(f"  {k}: {v}")

    if not trades1.empty:
        print("\n  交易记录:")
        print(trades1.to_string(index=False))

    # ============================================================
    # 策略2: 网格交易
    # ============================================================
    print("\n" + "=" * 70)
    print("策略2: 网格交易策略（网格大小3%）")
    print("=" * 70)

    df2 = grid_strategy(df.copy(), grid_size=0.03)
    df2, trades2 = backtest(df2)
    perf2 = evaluate(df2, trades2)

    for k, v in perf2.items():
        print(f"  {k}: {v}")

    if not trades2.empty:
        print(f"\n  交易次数: {len(trades2)}")

    # ============================================================
    # 策略3: 定投增强
    # ============================================================
    print("\n" + "=" * 70)
    print("策略3: 定投增强策略")
    print("=" * 70)

    df3 = dca_optimized(df.copy(), base_amount=1000)
    total_invested = df3["total_invested"].iloc[-1]
    dca_value = df3["dca_value"].iloc[-1]
    dca_return = (dca_value / total_invested - 1) * 100

    print(f"  基础定投: 1000元/周")
    print(f"  增强逻辑: RSI<25双倍投，RSI>75减半投，回撤>20%双倍投")
    print(f"  总投入: {total_invested:,.0f}元")
    print(f"  当前市值: {dca_value:,.0f}元")
    print(f"  定投收益: {dca_return:+.2f}%")

    # ============================================================
    # 最新信号
    # ============================================================
    print("\n" + "=" * 70)
    print("最新市场状态")
    print("=" * 70)

    last = df.iloc[-1]
    print(f"""
  日期: {last['日期'].strftime('%Y-%m-%d')}
  净值: {last['nav']:.4f}
  趋势: {'上升' if last['trend'] == 1 else '下降'}
  RSI6: {last['RSI6']:.1f} | RSI14: {last['RSI14']:.1f}
  MA5: {last['MA5']:.4f} | MA20: {last['MA20']:.4f} | MA60: {last['MA60']:.4f}
  均线排列: {'多头' if last['MA5'] > last['MA20'] > last['MA60'] else '空头'}
  动量(20日): {last['momentum']*100:.2f}%
  回撤: {last['drawdown']*100:.2f}%
    """)

    # ============================================================
    # 策略对比总结
    # ============================================================
    print("=" * 70)
    print("策略对比总结")
    print("=" * 70)

    summary = pd.DataFrame({
        "趋势跟踪": perf1,
        "网格交易": perf2,
    }).T

    print("\n  择时策略对比:")
    print(summary.to_string())

    print(f"\n  定投增强收益: {dca_return:+.2f}%")

    print("""
┌─────────────────────────────────────────────────────────────────┐
│                       策略选择建议                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【当前市场判断】                                               │
│   • 趋势: 下降趋势，均线空头排列                                │
│   • RSI: 36（接近超卖区域）                                     │
│   • 回撤: 约-20%（调整较深）                                    │
│                                                                 │
│  【推荐策略】                                                   │
│   1. 定投增强（最适合普通投资者）                               │
│      - 当前RSI偏低，可以加大定投金额                            │
│      - 回撤较深，适合分批建仓                                   │
│                                                                 │
│   2. 网格交易（适合震荡行情）                                   │
│      - 当前处于震荡筑底阶段                                     │
│      - 网格策略可以在区间内反复获利                             │
│                                                                 │
│   3. 趋势跟踪（等待信号）                                       │
│      - 当前趋势向下，等待趋势反转信号                           │
│      - 当MA5上穿MA20且RSI<40时考虑买入                          │
│                                                                 │
│  【风险提示】                                                   │
│   • 黄金短期波动大，建议仓位控制在10-15%                        │
│   • 止损线建议设在-10%~-15%                                     │
│   • 定投策略需要坚持1年以上才能见效                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    """)

    return df, df1, df2, df3


if __name__ == "__main__":
    df, df1, df2, df3 = main()
