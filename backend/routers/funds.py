from fastapi import APIRouter, HTTPException
from services.data_fetcher import (
    get_all_funds, get_fund_nav, refresh_fund, load_fund_data_to_df,
    add_fund, update_fund, delete_fund, search_fund_by_code
)
from models import FundInfo, FundCreate, FundUpdate, FundNavResponse, NavData

router = APIRouter(prefix="/api/funds", tags=["funds"])


@router.get("", response_model=list[FundInfo])
def list_funds():
    funds = get_all_funds()
    return [FundInfo(**f) for f in funds]


@router.post("", response_model=FundInfo)
def create_fund(req: FundCreate):
    existing = get_all_funds()
    if any(f["code"] == req.code for f in existing):
        raise HTTPException(status_code=400, detail=f"基金 {req.code} 已存在")

    # 尝试自动拉取数据
    try:
        records = refresh_fund(req.code, days=180)
        if not records:
            raise HTTPException(status_code=400, detail=f"基金代码 {req.code} 无效，无法获取数据")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"验证基金代码失败: {str(e)}")

    fund = add_fund(req.code, req.name, req.fund_type)
    return fund


@router.put("/{code}", response_model=FundInfo)
def update_fund_info(code: str, req: FundUpdate):
    try:
        fund = update_fund(code, name=req.name, fund_type=req.fund_type)
        return fund
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{code}")
def delete_fund_item(code: str):
    success = delete_fund(code)
    if not success:
        raise HTTPException(status_code=404, detail=f"基金 {code} 不存在")
    return {"message": f"基金 {code} 已删除"}


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
    # 如果基金不存在，自动注册
    funds = get_all_funds()
    if not any(f["code"] == code for f in funds):
        info = search_fund_by_code(code)
        if info:
            add_fund(code, info["name"], info.get("fund_type", "其他"))
        else:
            add_fund(code, f"基金{code}", "其他")

    try:
        records = refresh_fund(code, days)
        return {"code": code, "records_fetched": len(records), "message": "数据刷新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")
