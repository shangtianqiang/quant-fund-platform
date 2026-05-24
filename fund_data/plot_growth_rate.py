import json
from pyecharts.charts import Line, Tab
from pyecharts import options as opts
from pyecharts.globals import ThemeType

base_path = "C:/Users/FOH/Desktop/量化投资/fund_data/"

funds = [
    ("000217", "华安黄金ETF联接C"),
    ("004253", "国泰黄金ETF联接C"),
    ("002611", "博时黄金ETF联接C"),
    ("002963", "易方达黄金ETF联接C"),
]


def build_fund_chart(code: str, name: str) -> Line:
    with open(f"{base_path}{code}_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x["FSRQ"])

    dates = [d["FSRQ"] for d in data]
    growth_rates = [float(d["JZZZL"]) for d in data]
    nav_values = [float(d["DWJZ"]) for d in data]

    line = Line(init_opts=opts.InitOpts(
        theme=ThemeType.LIGHT,
        width="1100px",
        height="500px",
    ))

    line.add_xaxis(dates)

    # 日增长率
    line.add_yaxis(
        "日增长率(%)",
        growth_rates,
        is_smooth=True,
        symbol_size=3,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=1.5),
        areastyle_opts=opts.AreaStyleOpts(opacity=0.15),
    )

    # 单位净值（次坐标轴）
    line.add_yaxis(
        "单位净值",
        nav_values,
        is_smooth=True,
        symbol_size=3,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=1.5, type_="dashed"),
        yaxis_index=1,
    )

    line.set_global_opts(
        title_opts=opts.TitleOpts(
            title=f"{name}({code})",
            subtitle="日增长率 & 单位净值走势",
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        legend_opts=opts.LegendOpts(pos_top="8%"),
        datazoom_opts=[
            opts.DataZoomOpts(type_="slider", range_start=0, range_end=100),
            opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
        ],
        xaxis_opts=opts.AxisOpts(name="日期"),
    )

    line.set_series_opts(
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值"),
            ]
        ),
    )

    # 双Y轴
    line.extend_axis(
        yaxis=opts.AxisOpts(
            name="单位净值",
            position="right",
            splitline_opts=opts.SplitLineOpts(is_show=False),
        )
    )
    line.set_global_opts(
        yaxis_opts=opts.AxisOpts(name="日增长率(%)", position="left"),
    )

    return line


# 构建Tab
tab = Tab(page_title="黄金ETF联接基金 增长率分析")

for code, name in funds:
    chart = build_fund_chart(code, name)
    tab.add(chart, name)

tab.render(f"{base_path}黄金ETF联接基金_增长率分析.html")
print("图表已生成: " + base_path + "黄金ETF联接基金_增长率分析.html")
