# 黄金ETF量化投资平台

基于 FastAPI + Next.js 构建的黄金ETF联接基金量化分析、策略回测与信号监控平台。

## 功能特性

- **基金管理** — 查看华安/国泰/博时/易方达黄金ETF联接基金净值走势，一键刷新数据
- **策略回测** — 内置 4 种量化策略，支持自定义参数回测
- **信号监控** — 实时技术指标（RSI、MACD、均线、布林带），自动判断趋势和买卖信号
- **可视化看板** — ECharts 交互式图表，净值曲线、买卖信号标记、绩效指标展示

## 内置策略

| 策略 | 说明 |
|------|------|
| 多因子择时 | 综合 MA、RSI、MACD、布林带多因子，满足 3 个以上条件触发交易，8% 止损 |
| 趋势跟踪 | 趋势感知策略，上升趋势积极买入，下降趋势谨慎操作 |
| 网格交易 | 每跌 3% 加仓一次，每涨 3% 减仓一次，适合震荡行情 |
| 定投增强 | 每周定投，RSI 低多投、RSI 高少投，趋势 + 回撤动态调整金额 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + SQLite + pandas + numpy |
| 前端 | Next.js 14 + React 18 + TypeScript + TailwindCSS + ECharts |
| 数据 | 天天基金 API |

## 项目结构

```
├── backend/                  # FastAPI 后端
│   ├── main.py               # 入口
│   ├── database.py           # SQLite 数据库
│   ├── models.py             # 数据模型
│   ├── routers/              # API 路由
│   │   ├── funds.py          # 基金数据
│   │   ├── strategies.py     # 策略回测
│   │   └── signals.py        # 实时信号
│   └── services/             # 业务逻辑
│       ├── data_fetcher.py   # 数据获取
│       ├── indicator_engine.py # 技术指标
│       ├── strategy_engine.py  # 策略引擎
│       └── backtester.py     # 回测引擎
├── frontend/                 # Next.js 前端
│   ├── app/
│   │   ├── page.tsx          # 策略总览
│   │   ├── funds/page.tsx    # 基金管理
│   │   ├── strategies/page.tsx # 策略回测
│   │   └── signals/page.tsx  # 信号监控
│   └── components/           # 图表、卡片组件
└── fund_data/                # 历史数据文件
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 终端 1 — 启动后端
cd backend
uvicorn main:app --reload --port 8000

# 终端 2 — 启动前端
cd frontend
npm run dev
```

访问 http://localhost:3000

### API 文档

启动后端后访问 http://localhost:8000/docs

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/funds | 基金列表 |
| GET | /api/funds/{code}/nav | 基金净值数据 |
| POST | /api/funds/{code}/refresh | 刷新基金数据 |
| GET | /api/strategies | 策略列表 |
| POST | /api/strategies/run | 运行策略回测 |
| GET | /api/signals | 所有基金最新信号 |
| GET | /api/signals/{code} | 单只基金信号 |

## 截图

| 策略总览 | 策略回测 |
|---------|---------|
| ![总览](docs/dashboard.png) | ![回测](docs/backtest.png) |

## License

MIT
