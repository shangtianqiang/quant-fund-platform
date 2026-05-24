from fastapi import APIRouter, HTTPException
from services.data_fetcher import get_all_funds, get_fund_nav, refresh_fund, load_fund_data_to_df
from models import FundInfo, FundNavResponse, NavData

router = APIRouter(prefix="/api/funds", tags=["funds"])


@router.get("", response_model=list[FundInfo])
def list_funds():
    funds = get_all_funds()
    return [FundInfo(**f) for f in funds]


@router.get("/{code}/nav")
def fund_nav(code: str, start_date: str = None, end_date: str = None):
    df = get_fund_nav(code, start_date, end_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"基金 {code} 无数据，请先刷新")

    nav_list = []
    for _, row in df.iterrows():
        nav_list.append({
            "date": row["date"],
            "nav": row["nav"],
            "daily_return": row["daily_return"],
        })

    latest_nav = df.iloc[-1]["nav"]
    first_nav = df.iloc[0]["nav"]
    half_year_return = round((latest_nav / first_nav - 1) * 100, 2)

    funds = get_all_funds()
    fund_info = next((f for f in funds if f["code"] == code), None)

    return {
        "fund": fund_info,
        "data": nav_list,
        "latest_nav": latest_nav,
        "half_year_return": half_year_return,
    }


@router.post("/{code}/refresh")
def refresh_fund_data(code: str, days: int = 180):
    try:
        records = refresh_fund(code, days)
        return {"code": code, "records_fetched": len(records), "message": "数据刷新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")
