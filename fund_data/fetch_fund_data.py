import requests
import json
import csv
import os
from datetime import datetime, timedelta

# 基金配置
FUNDS = [
    {"code": "000217", "name": "华安黄金ETF联接C"},
    {"code": "004253", "name": "国泰黄金ETF联接C"},
    {"code": "002611", "name": "博时黄金ETF联接C"},
    {"code": "002963", "name": "易方达黄金ETF联接C"},
]

API_URL = "http://api.fund.eastmoney.com/f10/lsjz"
HEADERS = {"Referer": "http://fund.eastmoney.com/"}
PAGE_SIZE = 20


def fetch_fund_data(code: str, start_date: str, end_date: str) -> list[dict]:
    """获取单只基金的历史净值数据"""
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
            print(f"  API错误: {result.get('ErrMsg')}")
            break

        data = result.get("Data", {})
        records = data.get("LSJZList", [])
        if not records:
            break

        all_data.extend(records)
        total = result.get("TotalCount", 0)
        print(f"  第{page}页, 已获取{len(all_data)}/{total}条")
        if len(all_data) >= total:
            break
        page += 1

    return all_data


def save_json(data: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(funds_data: dict[str, list[dict]], path: str):
    # 按日期排序，收集所有日期
    for code in funds_data:
        funds_data[code].sort(key=lambda x: x["FSRQ"])
    dates = sorted({d["FSRQ"] for records in funds_data.values() for d in records}, reverse=True)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # 表头
        header = ["日期"]
        for fund in FUNDS:
            header.extend([f"{fund['name']}({fund['code']})_单位净值", "日增长率"])
        writer.writerow(header)
        # 数据行
        for date in dates:
            row = [date]
            for fund in FUNDS:
                record = next((d for d in funds_data[fund["code"]] if d["FSRQ"] == date), None)
                if record:
                    row.extend([record["DWJZ"], record["JZZZL"] + "%"])
                else:
                    row.extend(["", ""])
            writer.writerow(row)


def print_summary(funds_data: dict[str, list[dict]]):
    print("\n" + "=" * 60)
    print("基金数据汇总")
    print("=" * 60)
    for fund in FUNDS:
        records = funds_data[fund["code"]]
        if not records:
            print(f"\n{fund['name']}({fund['code']}): 无数据")
            continue

        records.sort(key=lambda x: x["FSRQ"])
        first, last = records[0], records[-1]
        half_year_ret = (float(last["DWJZ"]) / float(first["DWJZ"]) - 1) * 100

        print(f"\n{fund['name']}({fund['code']})")
        print(f"  数据区间: {first['FSRQ']} ~ {last['FSRQ']} ({len(records)}条)")
        print(f"  期初净值: {first['DWJZ']}")
        print(f"  最新净值: {last['DWJZ']}")
        print(f"  半年涨幅: {half_year_ret:+.2f}%")


def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    output_dir = os.path.dirname(os.path.abspath(__file__))
    funds_data = {}

    print(f"获取基金数据: {start_date} ~ {end_date}\n")

    for fund in FUNDS:
        print(f"正在获取 {fund['name']}({fund['code']})...")
        records = fetch_fund_data(fund["code"], start_date, end_date)
        funds_data[fund["code"]] = records

        # 保存单只基金JSON
        json_path = os.path.join(output_dir, f"{fund['code']}_full.json")
        save_json(records, json_path)
        print(f"  已保存: {json_path}")

    # 保存合并CSV
    csv_path = os.path.join(output_dir, "黄金ETF联接基金_半年数据.csv")
    save_csv(funds_data, csv_path)
    print(f"\n合并CSV: {csv_path}")

    print_summary(funds_data)


if __name__ == "__main__":
    main()
