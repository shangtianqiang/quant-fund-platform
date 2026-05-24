import json
from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.globals import ThemeType

base_path = "C:/Users/FOH/Desktop/量化投资/fund_data/"

funds = [
    ("000217", "华安黄金ETF联接C"),
    ("004253", "国泰黄金ETF联接C"),
    ("002611", "博时黄金ETF联接C"),
    ("002963", "易方达黄金ETF联接C"),
]

all_data = {}
for code, name in funds:
    with open(f"{base_path}{code}_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x["FSRQ"])
    all_data[code] = {d["FSRQ"]: float(d["DWJZ"]) for d in data}

dates = sorted(set().union(*[d.keys() for d in all_data.values()]))

line = Line(init_opts=opts.InitOpts(
    theme=ThemeType.LIGHT,
    width="1200px",
    height="600px",
    page_title="黄金ETF联接基金半年净值走势"
))

line.add_xaxis(dates)

for code, name in funds:
    values = [all_data[code].get(date) for date in dates]
    line.add_yaxis(
        name,
        values,
        is_smooth=True,
        symbol_size=4,
        label_opts=opts.LabelOpts(is_show=False),
    )

line.set_global_opts(
    title_opts=opts.TitleOpts(
        title="黄金ETF联接基金 半年净值走势",
        subtitle="2025.11.24 ~ 2026.05.21",
    ),
    tooltip_opts=opts.TooltipOpts(trigger="axis"),
    legend_opts=opts.LegendOpts(pos_top="5%"),
    datazoom_opts=[
        opts.DataZoomOpts(type_="slider", range_start=0, range_end=100),
        opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
    ],
    yaxis_opts=opts.AxisOpts(name="单位净值"),
    xaxis_opts=opts.AxisOpts(name="日期"),
)

line.render(f"{base_path}黄金ETF联接基金_净值走势图.html")
print("图表已生成: " + base_path + "黄金ETF联接基金_净值走势图.html")
