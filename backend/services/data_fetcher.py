import requests
import pandas as pd
from datetime import datetime, timedelta
from database import get_db

API_URL = "http://api.fund.eastmoney.com/f10/lsjz"
HEADERS = {"Referer": "http://fund.eastmoney.com/"}
PAGE_SIZE = 20


def fetch_fund_data(code: str, start_date: str, end_date: str) -> list[dict]:
    all_data = []
    page = 1
    while True:
        params = {
            "fundCode": code,
            "pageIndex": page,
            "pageSize": PAGE_SIZE,
            "startDate": start_date,
            "endDate": end_date,
        }
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ErrCode") != 0:
            break
        data = result.get("Data", {})
        records = data.get("LSJZList", [])
        if not records:
            break
        all_data.extend(records)
        total = result.get("TotalCount", 0)
        if len(all_data) >= total:
            break
        page += 1
    return all_data


def save_to_db(code: str, records: list[dict]):
    with get_db() as conn:
        for r in records:
            conn.execute(
                """INSERT OR REPLACE INTO fund_nav (code, date, nav, cumulative_nav, daily_return)
                   VALUES (?, ?, ?, ?, ?)""",
                (code, r["FSRQ"], float(r["DWJZ"]),
                 float(r["LJJZ"]) if r.get("LJJZ") else None,
                 float(r["JZZZL"]) if r.get("JZZZL") else None)
            )


def refresh_fund(code: str, days: int = 180) -> list[dict]:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    records = fetch_fund_data(code, start_date, end_date)
    if records:
        save_to_db(code, records)
    return records


def get_fund_nav(code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    with get_db() as conn:
        query = "SELECT * FROM fund_nav WHERE code = ?"
        params = [code]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date"
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_all_funds() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM funds ORDER BY code").fetchall()
    return [dict(r) for r in rows]


def add_fund(code: str, name: str, fund_type: str = "其他") -> dict:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO funds (code, name, fund_type) VALUES (?, ?, ?)",
            (code, name, fund_type)
        )
    return {"code": code, "name": name, "fund_type": fund_type}


def update_fund(code: str, name: str = None, fund_type: str = None) -> dict:
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM funds WHERE code = ?", (code,)).fetchone()
        if not existing:
            raise ValueError(f"基金 {code} 不存在")
        if name:
            conn.execute("UPDATE funds SET name = ? WHERE code = ?", (name, code))
        if fund_type:
            conn.execute("UPDATE funds SET fund_type = ? WHERE code = ?", (fund_type, code))
        updated = conn.execute("SELECT * FROM funds WHERE code = ?", (code,)).fetchone()
    return dict(updated)


def delete_fund(code: str) -> bool:
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM funds WHERE code = ?", (code,)).fetchone()
        if not existing:
            return False
        conn.execute("DELETE FROM fund_nav WHERE code = ?", (code,))
        conn.execute("DELETE FROM funds WHERE code = ?", (code,))
    return True


def search_fund_by_code(code: str) -> dict | None:
    """从东方财富 API 查询基金名称"""
    try:
        url = f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
        params = {"m": 1, "key": code}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("Datas"):
            for item in data["Datas"]:
                if item.get("CODE") == code:
                    return {"code": code, "name": item.get("NAME", ""), "fund_type": item.get("FundBaseInfo", {}).get("FTYPE", "其他")}
    except Exception:
        pass
    return None


def load_fund_data_to_df(code: str) -> pd.DataFrame:
    df = get_fund_nav(code)
    if df.empty:
        records = refresh_fund(code)
        if records:
            df = get_fund_nav(code)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df.rename(columns={"nav": "nav", "daily_return": "daily_return"}, inplace=True)
    return df
