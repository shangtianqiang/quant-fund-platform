"""
黄金ETF联接基金量化策略
策略类型：多因子择时 + 动态仓位管理
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# 1. 数据加载与预处理
# ============================================================

def load_data(filepath: str) -> pd.DataFrame:
    """加载CSV数据并预处理"""
    df = pd.read_csv(filepath)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    # 提取净值列（选择华安作为主交易标的）
    nav_col = "华安黄金ETF联接C(000217)_单位净值"
    df["nav"] = df[nav_col].astype(float)

    # 计算日收益率
    df["daily_return"] = df["nav"].pct_change()

    return df


# ============================================================
# 2. 技术指标计算
# ============================================================

def calc_ma(df: pd.DataFrame, col: str = "nav", periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """计算移动平均线"""
    for p in periods:
        df[f"MA{p}"] = df[col].rolling(window=p).mean()
    return df


def calc_rsi(df: pd.DataFrame, col: str = "nav", period: int = 14) -> pd.DataFrame:
    """计算RSI相对强弱指标"""
    delta = df[col].diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


def calc_macd(df: pd.DataFrame, col: str = "nav",
              fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算MACD指标"""
    ema_fast = df[col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[col].ewm(span=slow, adjust=False).mean()

    df["MACD_DIF"] = ema_fast - ema_slow
    df["MACD_DEA"] = df["MACD_DIF"].ewm(span=signal, adjust=False).mean()
    df["MACD_HIST"] = 2 * (df["MACD_DIF"] - df["MACD_DEA"])

    return df


def calc_bollinger(df: pd.DataFrame, col: str = "nav", period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """计算布林带"""
    df["BB_MID"] = df[col].rolling(window=period).mean()
    bb_std = df[col].rolling(window=period).std()
    df["BB_UPPER"] = df["BB_MID"] + std_dev * bb_std
    df["BB_LOWER"] = df["BB_MID"] - std_dev * bb_std

    return df


def calc_drawdown(df: pd.DataFrame, col: str = "nav") -> pd.DataFrame:
    """计算回撤"""
    df["cummax"] = df[col].cummax()
    df["drawdown"] = (df[col] - df["cummax"]) / df["cummax"]
    return df


def calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标"""
    df = calc_ma(df)
    df = calc_rsi(df)
    df = calc_macd(df)
    df = calc_bollinger(df)
    df = calc_drawdown(df)
    return df


# ============================================================
# 3. 信号生成（多因子综合）
# ============================================================

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成交易信号
    信号值：1=买入, -1=卖出, 0=持有
    """
    df["signal"] = 0

    # --- 买入条件（满足2个以上触发） ---
    buy_conditions = pd.DataFrame()

    # 条件1：MA5上穿MA20（金叉）
    buy_conditions["ma_cross"] = (
        (df["MA5"] > df["MA20"]) &
        (df["MA5"].shift(1) <= df["MA20"].shift(1))
    ).astype(int)

    # 条件2：RSI超卖区域（<35）
    buy_conditions["rsi_oversold"] = (df["RSI"] < 35).astype(int)

    # 条件3：价格触及布林带下轨后反弹
    buy_conditions["bb_bounce"] = (
        (df["nav"] > df["BB_LOWER"]) &
        (df["nav"].shift(1) <= df["BB_LOWER"].shift(1))
    ).astype(int)

    # 条件4：MACD金叉
    buy_conditions["macd_cross"] = (
        (df["MACD_DIF"] > df["MACD_DEA"]) &
        (df["MACD_DIF"].shift(1) <= df["MACD_DEA"].shift(1))
    ).astype(int)

    # 条件5：价格站上MA20
    buy_conditions["above_ma20"] = (df["nav"] > df["MA20"]).astype(int)

    # 综合买入信号（满足2个以上条件）
    buy_score = buy_conditions.sum(axis=1)
    buy_signal = buy_score >= 2

    # --- 卖出条件（满足2个以上触发） ---
    sell_conditions = pd.DataFrame()

    # 条件1：MA5下穿MA20（死叉）
    sell_conditions["ma_cross"] = (
        (df["MA5"] < df["MA20"]) &
        (df["MA5"].shift(1) >= df["MA20"].shift(1))
    ).astype(int)

    # 条件2：RSI超买区域（>70）
    sell_conditions["rsi_overbought"] = (df["RSI"] > 70).astype(int)

    # 条件3：价格触及布林带上轨后回落
    sell_conditions["bb_reject"] = (
        (df["nav"] < df["BB_UPPER"]) &
        (df["nav"].shift(1) >= df["BB_UPPER"].shift(1))
    ).astype(int)

    # 条件4：MACD死叉
    sell_conditions["macd_cross"] = (
        (df["MACD_DIF"] < df["MACD_DEA"]) &
        (df["MACD_DIF"].shift(1) >= df["MACD_DEA"].shift(1))
    ).astype(int)

    # 综合卖出信号（满足2个以上条件）
    sell_score = sell_conditions.sum(axis=1)
    sell_signal = sell_score >= 2

    # --- 止损条件 ---
    stop_loss = df["drawdown"] < -0.08  # 回撤超过8%

    # --- 应用信号 ---
    df.loc[buy_signal, "signal"] = 1
    df.loc[sell_signal, "signal"] = -1
    df.loc[stop_loss, "signal"] = -1  # 止损强制卖出

    # 记录信号得分（用于分析）
    df["buy_score"] = buy_score
    df["sell_score"] = sell_score

    return df


# ============================================================
# 4. 回测引擎
# ============================================================

class Backtester:
    """回测引擎"""

    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 手续费率

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行回测"""
        capital = self.initial_capital
        position = 0  # 持有份额
        total_value = []  # 每日总资产
        trades = []  # 交易记录

        for i, row in df.iterrows():
            nav = row["nav"]
            signal = row["signal"]

            # 买入信号且无持仓
            if signal == 1 and position == 0:
                # 全仓买入
                shares = capital / (nav * (1 + self.commission))
                cost = shares * nav * (1 + self.commission)
                if cost <= capital:
                    position = shares
                    capital -= cost
                    trades.append({
                        "date": row["日期"],
                        "action": "BUY",
                        "price": nav,
                        "shares": shares,
                        "cost": cost
                    })

            # 卖出信号且有持仓
            elif signal == -1 and position > 0:
                # 全仓卖出
                revenue = position * nav * (1 - self.commission)
                capital += revenue
                trades.append({
                    "date": row["日期"],
                    "action": "SELL",
                    "price": nav,
                    "shares": position,
                    "revenue": revenue
                })
                position = 0

            # 计算当日总资产
            current_value = capital + position * nav
            total_value.append(current_value)

        df["total_value"] = total_value
        df["strategy_return"] = df["total_value"].pct_change()

        self.trades = pd.DataFrame(trades) if trades else pd.DataFrame()
        return df


# ============================================================
# 5. 绩效评估
# ============================================================

def calc_performance(df: pd.DataFrame, initial_capital: float = 100000) -> dict:
    """计算策略绩效指标"""
    # 基准收益（买入持有）
    benchmark_return = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100

    # 策略收益
    strategy_return = (df["total_value"].iloc[-1] / initial_capital - 1) * 100

    # 年化收益
    days = (df["日期"].iloc[-1] - df["日期"].iloc[0]).days
    annual_return = ((1 + strategy_return / 100) ** (365 / days) - 1) * 100

    # 最大回撤
    cummax = df["total_value"].cummax()
    drawdown = (df["total_value"] - cummax) / cummax
    max_drawdown = drawdown.min() * 100

    # 夏普比率（假设无风险利率2%）
    risk_free_rate = 0.02
    daily_returns = df["strategy_return"].dropna()
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() * 252 - risk_free_rate) / (daily_returns.std() * np.sqrt(252))
    else:
        sharpe = 0

    # 胜率
    if "signal" in df.columns:
        buy_signals = df[df["signal"] == 1]
        sell_signals = df[df["signal"] == -1]
        if len(buy_signals) > 0 and len(sell_signals) > 0:
            wins = 0
            total_trades = min(len(buy_signals), len(sell_signals))
            for i in range(total_trades):
                if sell_signals.iloc[i]["nav"] > buy_signals.iloc[i]["nav"]:
                    wins += 1
            win_rate = wins / total_trades * 100 if total_trades > 0 else 0
        else:
            win_rate = 0
    else:
        win_rate = 0

    return {
        "基准收益(买入持有)": f"{benchmark_return:.2f}%",
        "策略收益": f"{strategy_return:.2f}%",
        "年化收益": f"{annual_return:.2f}%",
        "最大回撤": f"{max_drawdown:.2f}%",
        "夏普比率": f"{sharpe:.2f}",
        "交易胜率": f"{win_rate:.1f}%",
        "交易天数": days,
    }


# ============================================================
# 6. 主程序
# ============================================================

def main():
    # 加载数据
    filepath = r"c:\Users\FOH\Desktop\量化投资\fund_data\黄金ETF联接基金_半年数据.csv"
    print("=" * 60)
    print("黄金ETF联接基金量化策略回测")
    print("=" * 60)

    df = load_data(filepath)
    print(f"\n数据区间: {df['日期'].iloc[0].strftime('%Y-%m-%d')} ~ {df['日期'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(df)}")

    # 计算技术指标
    df = calc_all_indicators(df)

    # 生成交易信号
    df = generate_signals(df)

    # 回测
    backtester = Backtester(initial_capital=100000, commission=0.001)
    df = backtester.run(df)

    # 输出绩效
    performance = calc_performance(df)
    print("\n" + "-" * 40)
    print("策略绩效:")
    print("-" * 40)
    for k, v in performance.items():
        print(f"  {k}: {v}")

    # 输出交易记录
    if not backtester.trades.empty:
        print("\n" + "-" * 40)
        print("交易记录:")
        print("-" * 40)
        print(backtester.trades.to_string(index=False))
    else:
        print("\n无交易记录")

    # 保存结果
    output_path = r"c:\Users\FOH\Desktop\量化投资\backtest_result.csv"
    df[["日期", "nav", "signal", "total_value", "strategy_return", "RSI", "MA5", "MA20"]].to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    print(f"\n回测结果已保存: {output_path}")

    return df, backtester.trades


if __name__ == "__main__":
    df, trades = main()
