import json

base_path = "C:/Users/FOH/Desktop/量化投资/fund_data/"

funds = [
    {"code": "000217", "name": "华安黄金ETF联接C"},
    {"code": "004253", "name": "国泰黄金ETF联接C"},
    {"code": "002611", "name": "博时黄金ETF联接C"},
    {"code": "002963", "name": "易方达黄金ETF联接C"},
]

# 加载数据并转为JS变量
all_series = {}
for fund in funds:
    with open(f"{base_path}{fund['code']}_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x["FSRQ"])
    all_series[fund["code"]] = {
        "dates": [d["FSRQ"] for d in data],
        "nav": [float(d["DWJZ"]) for d in data],
        "growth": [float(d["JZZZL"]) for d in data],
    }

funds_json = json.dumps(funds, ensure_ascii=False)
data_json = json.dumps(all_series, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>黄金ETF联接基金 综合分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  body {{ margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f7fa; }}
  .header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }}
  .header h1 {{ margin: 0; font-size: 20px; color: #333; }}
  select {{ padding: 8px 12px; font-size: 14px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; cursor: pointer; min-width: 200px; }}
  select:focus {{ outline: none; border-color: #409eff; }}
  #chart {{ width: 100%; height: 520px; background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
<div class="header">
  <h1>黄金ETF联接基金 净值 & 增长率</h1>
  <select id="fundSelect"></select>
</div>
<div id="chart"></div>

<script>
const funds = {funds_json};
const allData = {data_json};
const select = document.getElementById('fundSelect');

funds.forEach((f, i) => {{
  const opt = document.createElement('option');
  opt.value = f.code;
  opt.textContent = f.name + '(' + f.code + ')';
  if (i === 0) opt.selected = true;
  select.appendChild(opt);
}});

const chart = echarts.init(document.getElementById('chart'));

function render(code) {{
  const d = allData[code];
  const fund = funds.find(f => f.code === code);
  chart.setOption({{
    title: {{ text: fund.name + '(' + fund.code + ')', subtext: '净值 & 增长率', left: 'center' }},
    tooltip: {{ trigger: 'axis' }},
    legend: {{ top: 40, data: ['日增长率(%)', '单位净值'] }},
    grid: {{ top: 90, bottom: 80, left: 60, right: 60 }},
    dataZoom: [
      {{ type: 'slider', start: 0, end: 100 }},
      {{ type: 'inside', start: 0, end: 100 }}
    ],
    xAxis: {{ type: 'category', data: d.dates, name: '日期' }},
    yAxis: [
      {{ type: 'value', name: '单位净值', position: 'left' }},
      {{ type: 'value', name: '日增长率(%)', position: 'right' }}
    ],
    series: [
      {{
        name: '单位净值', type: 'line', data: d.nav, smooth: true, symbol: 'none',
        yAxisIndex: 0, lineStyle: {{ width: 2, color: '#333' }}, itemStyle: {{ color: '#333' }},
        markPoint: {{ data: [{{ type: 'max', name: '最大' }}, {{ type: 'min', name: '最小' }}] }},
      }},
      {{
        name: '日增长率(%)', type: 'line', data: d.growth, smooth: true, symbol: 'none',
        yAxisIndex: 1, lineStyle: {{ width: 1.5, color: '#c23531' }}, itemStyle: {{ color: '#c23531' }},
        areaStyle: {{ opacity: 0.1, color: '#c23531' }},
        markPoint: {{ data: [{{ type: 'max', name: '最大' }}, {{ type: 'min', name: '最小' }}] }},
      }}
    ]
  }}, true);
}}

select.addEventListener('change', () => render(select.value));
render(funds[0].code);
window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>"""

output = f"{base_path}黄金ETF联接基金_综合分析.html"
with open(output, "w", encoding="utf-8") as f:
    f.write(html)
print("图表已生成: " + output)
