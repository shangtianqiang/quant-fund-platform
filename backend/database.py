import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "quant_fund.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS funds (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                fund_type TEXT DEFAULT 'ETF联接',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS fund_nav (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                nav REAL NOT NULL,
                cumulative_nav REAL,
                daily_return REAL,
                UNIQUE(code, date),
                FOREIGN KEY (code) REFERENCES funds(code)
            );

            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                fund_code TEXT NOT NULL,
                run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                initial_capital REAL,
                benchmark_return REAL,
                strategy_return REAL,
                annual_return REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                win_rate REAL,
                trade_count INTEGER,
                equity_curve TEXT,
                FOREIGN KEY (fund_code) REFERENCES funds(code)
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                shares REAL,
                amount REAL,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(id)
            );

            CREATE INDEX IF NOT EXISTS idx_nav_code_date ON fund_nav(code, date);
            CREATE INDEX IF NOT EXISTS idx_trades_backtest ON trades(backtest_id);
        """)

        # 插入默认基金
        default_funds = [
            ("000217", "华安黄金ETF联接C"),
            ("004253", "国泰黄金ETF联接C"),
            ("002611", "博时黄金ETF联接C"),
            ("002963", "易方达黄金ETF联接C"),
        ]
        for code, name in default_funds:
            conn.execute(
                "INSERT OR IGNORE INTO funds (code, name) VALUES (?, ?)",
                (code, name)
            )
