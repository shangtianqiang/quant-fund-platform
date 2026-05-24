import json

base_path = "C:/Users/FOH/Desktop/量化投资/fund_data/"

with open(f"{base_path}strategy_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>黄金ETF量化策略看板</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f0f2f5; color:#333; }}
.header {{ background:linear-gradient(135deg,#1a1a2e,#16213e); color:#fff; padding:20px 30px; display:flex; align-items:center; justify-content:space-between; }}
.header h1 {{ font-size:22px; font-weight:600; }}
.header .date {{ font-size:13px; opacity:.7; }}
.container {{ max-width:1400px; margin:0 auto; padding:20px; }}

/* 导航栏 */
.nav {{ display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }}
.nav-btn {{ padding:8px 18px; border:none; border-radius:6px; background:#fff; color:#555; font-size:13px; cursor:pointer; box-shadow:0 1px 3px rgba(0,0,0,.08); transition:all .2s; }}
.nav-btn:hover {{ background:#e8f4fd; color:#1890ff; }}
.nav-btn.active {{ background:#1890ff; color:#fff; }}

/* 卡片 */
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:20px; }}
.card {{ background:#fff; border-radius:8px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.card .label {{ font-size:12px; color:#999; margin-bottom:6px; }}
.card .value {{ font-size:22px; font-weight:700; }}
.card .value.green {{ color:#52c41a; }}
.card .value.red {{ color:#f5222d; }}
.card .sub {{ font-size:11px; color:#bbb; margin-top:4px; }}

/* 图表 */
.chart-box {{ background:#fff; border-radius:8px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); margin-bottom:20px; }}
.chart-box h3 {{ font-size:15px; color:#333; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }}
.chart {{ width:100%; height:400px; }}

/* 信号面板 */
.signals {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; margin-bottom:20px; }}
.signal-card {{ background:#fff; border-radius:8px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.signal-card h4 {{ font-size:14px; margin-bottom:12px; color:#333; }}
.signal-row {{ display:flex; justify-content:space-between; padding:5px 0; font-size:13px; border-bottom:1px solid #f8f8f8; }}
.signal-row:last-child {{ border:none; }}
.signal-row .k {{ color:#999; }}
.signal-row .v {{ font-weight:500; }}
.tag {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:500; }}
.tag.up {{ background:#f6ffed; color:#52c41a; }}
.tag.down {{ background:#fff2f0; color:#f5222d; }}

/* 交易记录 */
.trades-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.trades-table th {{ background:#fafafa; padding:8px 12px; text-align:left; font-weight:600; color:#666; }}
.trades-table td {{ padding:8px 12px; border-bottom:1px solid #f0f0f0; }}
.trades-table .buy {{ color:#f5222d; font-weight:500; }}
.trades-table .sell {{ color:#52c41a; font-weight:500; }}
</style>
</head>
<body>

<div class="header">
  <h1>黄金ETF量化策略看板</h1>
  <div class="date">数据区间: {data['dates'][0]} ~ {data['dates'][-1]}</div>
</div>

<div class="container">
  <!-- 策略切换 -->
  <div class="nav" id="navBar"></div>

  <!-- 绩效卡片 -->
  <div class="cards" id="perfCards"></div>

  <!-- 净值+信号图 -->
  <div class="chart-box">
    <h3 id="equityTitle">策略净值曲线 & 买卖信号</h3>
    <div class="chart" id="equityChart"></div>
  </div>

  <!-- 定投策略 -->
  <div class="chart-box">
    <h3>定投增强策略（华安黄金）</h3>
    <div class="chart" id="dcaChart"></div>
  </div>

  <!-- 最新信号 -->
  <div class="chart-box">
    <h3>最新市场信号</h3>
    <div class="signals" id="signalPanel"></div>
  </div>

  <!-- 交易记录 -->
  <div class="chart-box">
    <h3 id="tradesTitle">交易记录</h3>
    <div id="tradesPanel" style="max-height:300px;overflow:auto;"></div>
  </div>
</div>

<script>
const D = {data_json};
const strategyNames = Object.keys(D.strategies);
let currentStrategy = strategyNames[0];

// ============ 导航栏 ============
const navBar = document.getElementById('navBar');
strategyNames.forEach(name => {{
  const btn = document.createElement('button');
  btn.className = 'nav-btn' + (name === currentStrategy ? ' active' : '');
  btn.textContent = name;
  btn.onclick = () => {{
    currentStrategy = name;
    navBar.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderAll();
  }};
  navBar.appendChild(btn);
}});

// ============ 绩效卡片 ============
function renderPerf() {{
  const perf = D.strategies[currentStrategy].perf;
  const cards = [
    {{ label:'策略收益', value:perf.strategy+'%', cls:perf.strategy>=0?'green':'red' }},
    {{ label:'基准收益(持有)', value:perf.benchmark+'%', cls:perf.benchmark>=0?'green':'red' }},
    {{ label:'年化收益', value:perf.annual+'%', cls:perf.annual>=0?'green':'red' }},
    {{ label:'最大回撤', value:perf.max_drawdown+'%', cls:'red' }},
    {{ label:'夏普比率', value:perf.sharpe, cls:perf.sharpe>=1?'green':'' }},
    {{ label:'胜率', value:perf.win_rate+'%', cls:perf.win_rate>=50?'green':'red' }},
    {{ label:'交易次数', value:perf.trade_count, cls:'' }},
    {{ label:'定投收益', value:D.dca.dca_return+'%', cls:D.dca.dca_return>=0?'green':'red' }},
  ];
  document.getElementById('perfCards').innerHTML = cards.map(c =>
    `<div class="card"><div class="label">${{c.label}}</div><div class="value ${{c.cls}}">${{c.value}}</div></div>`
  ).join('');
}}

// ============ 净值+信号图 ============
const eqChart = echarts.init(document.getElementById('equityChart'));

function renderEquity() {{
  const s = D.strategies[currentStrategy];
  const trades = s.trades;

  const buyPoints = trades.filter(t => t.action==='BUY').map(t => [t.date, t.price]);
  const sellPoints = trades.filter(t => t.action==='SELL').map(t => [t.date, t.price]);

  eqChart.setOption({{
    tooltip: {{ trigger:'axis' }},
    legend: {{ data:['单位净值','策略净值','买入','卖出'], top:5 }},
    grid: {{ top:40, bottom:60, left:60, right:60 }},
    dataZoom: [{{ type:'slider',start:0,end:100 }},{{ type:'inside' }}],
    xAxis: {{ type:'category', data:D.dates }},
    yAxis: [
      {{ type:'value', name:'净值', position:'left' }},
      {{ type:'value', name:'策略净值', position:'right' }}
    ],
    series: [
      {{
        name:'单位净值', type:'line', data:s.nav, smooth:true, symbol:'none',
        lineStyle:{{width:1.5,color:'#333'}}, itemStyle:{{color:'#333'}}
      }},
      {{
        name:'策略净值', type:'line', data:s.equity_curve, smooth:true, symbol:'none',
        yAxisIndex:1, lineStyle:{{width:2,color:'#c23531'}}, itemStyle:{{color:'#c23531'}},
        areaStyle:{{opacity:.08,color:'#c23531'}}
      }},
      {{
        name:'买入', type:'scatter', data:buyPoints, symbol:'triangle', symbolSize:12,
        itemStyle:{{color:'#f5222d'}}, label:{{show:false}}
      }},
      {{
        name:'卖出', type:'scatter', data:sellPoints, symbol:'diamond', symbolSize:12,
        itemStyle:{{color:'#52c41a'}}, label:{{show:false}}
      }}
    ]
  }}, true);

  document.getElementById('equityTitle').textContent = currentStrategy + ' — 净值曲线 & 买卖信号';
}}

// ============ 定投图 ============
const dcaChart = echarts.init(document.getElementById('dcaChart'));
function renderDCA() {{
  dcaChart.setOption({{
    tooltip: {{ trigger:'axis' }},
    legend: {{ data:['累计投入','持仓市值'], top:5 }},
    grid: {{ top:40, bottom:60, left:60, right:60 }},
    dataZoom: [{{ type:'slider',start:0,end:100 }},{{ type:'inside' }}],
    xAxis: {{ type:'category', data:D.dates }},
    yAxis: {{ type:'value', name:'金额(元)' }},
    series: [
      {{
        name:'累计投入', type:'line', data:D.dca.invest_curve, smooth:true, symbol:'none',
        lineStyle:{{width:2,color:'#333'}}, itemStyle:{{color:'#333'}},
        areaStyle:{{opacity:.06,color:'#333'}}
      }},
      {{
        name:'持仓市值', type:'line', data:D.dca.value_curve, smooth:true, symbol:'none',
        lineStyle:{{width:2,color:'#c23531'}}, itemStyle:{{color:'#c23531'}},
        areaStyle:{{opacity:.08,color:'#c23531'}}
      }}
    ]
  }}, true);
}}

// ============ 信号面板 ============
function renderSignals() {{
  let html = '';
  for (const [name, sig] of Object.entries(D.latest_signals)) {{
    const trendCls = sig.trend==='上升' ? 'up' : 'down';
    const ddCls = sig.drawdown < -10 ? 'red' : '';
    html += `
    <div class="signal-card">
      <h4>${{name}}</h4>
      <div class="signal-row"><span class="k">最新净值</span><span class="v">${{sig.nav}}</span></div>
      <div class="signal-row"><span class="k">趋势</span><span class="v"><span class="tag ${{trendCls}}">${{sig.trend}}</span></span></div>
      <div class="signal-row"><span class="k">RSI(6/14)</span><span class="v">${{sig.rsi6}} / ${{sig.rsi14}}</span></div>
      <div class="signal-row"><span class="k">MA5/MA20/MA60</span><span class="v">${{sig.ma5}} / ${{sig.ma20}} / ${{sig.ma60}}</span></div>
      <div class="signal-row"><span class="k">回撤</span><span class="v" style="color:#f5222d">${{sig.drawdown}}%</span></div>
      <div class="signal-row"><span class="k">动量(20日)</span><span class="v">${{sig.momentum!=null ? sig.momentum+'%' : 'N/A'}}</span></div>
    </div>`;
  }}
  document.getElementById('signalPanel').innerHTML = html;
}}

// ============ 交易记录 ============
function renderTrades() {{
  const trades = D.strategies[currentStrategy].trades;
  document.getElementById('tradesTitle').textContent = currentStrategy + ' — 交易记录';
  if (!trades.length) {{
    document.getElementById('tradesPanel').innerHTML = '<p style="color:#999;padding:12px">无交易记录</p>';
    return;
  }}
  let html = '<table class="trades-table"><tr><th>日期</th><th>操作</th><th>价格</th></tr>';
  trades.forEach(t => {{
    const cls = t.action==='BUY' ? 'buy' : 'sell';
    const label = t.action==='BUY' ? '买入' : '卖出';
    html += `<tr><td>${{t.date}}</td><td class="${{cls}}">${{label}}</td><td>${{t.price}}</td></tr>`;
  }});
  html += '</table>';
  document.getElementById('tradesPanel').innerHTML = html;
}}

// ============ 渲染全部 ============
function renderAll() {{
  renderPerf();
  renderEquity();
  renderDCA();
  renderSignals();
  renderTrades();
}}

renderAll();
window.addEventListener('resize', () => {{ eqChart.resize(); dcaChart.resize(); }});
</script>
</body>
</html>"""

output = f"{base_path}黄金ETF量化策略看板.html"
with open(output, "w", encoding="utf-8") as f:
    f.write(html)
print("看板已生成: " + output)
