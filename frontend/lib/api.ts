import axios from "axios"

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
})

export interface FundInfo {
  code: string
  name: string
  fund_type: string
}

export interface NavData {
  date: string
  nav: number
  daily_return: number | null
}

export interface FundNavResponse {
  fund: FundInfo
  data: NavData[]
  latest_nav: number
  half_year_return: number
}

export interface StrategyInfo {
  name: string
  description: string
}

export interface PerformanceResult {
  benchmark_return: number
  strategy_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
  trade_count: number
}

export interface TradeRecord {
  date: string
  action: string
  price: number
  shares?: number
  amount?: number
}

export interface BacktestResult {
  strategy_name: string
  fund_code: string
  type: "timing" | "dca"
  perf: PerformanceResult | { total_invested: number; dca_value: number; dca_return: number }
  dates: string[]
  equity_curve?: number[]
  invest_curve?: number[]
  value_curve?: number[]
  nav: number[]
  trades: TradeRecord[]
}

export interface SignalData {
  code: string
  name: string
  nav: number
  rsi6: number | null
  rsi14: number | null
  ma5: number | null
  ma20: number | null
  ma60: number | null
  trend: string
  drawdown: number
  momentum: number | null
}

export const fundApi = {
  list: () => api.get<FundInfo[]>("/api/funds").then((r) => r.data),
  getNav: (code: string, startDate?: string, endDate?: string) => {
    const params: Record<string, string> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get<FundNavResponse>(`/api/funds/${code}/nav`, { params }).then((r) => r.data)
  },
  refresh: (code: string) => api.post(`/api/funds/${code}/refresh`).then((r) => r.data),
}

export const strategyApi = {
  list: () => api.get<StrategyInfo[]>("/api/strategies").then((r) => r.data),
  run: (data: { strategy_name: string; fund_code: string; initial_capital?: number }) =>
    api.post<BacktestResult>("/api/strategies/run", data).then((r) => r.data),
  results: (limit?: number) =>
    api.get("/api/strategies/results", { params: { limit: limit || 10 } }).then((r) => r.data),
}

export const signalApi = {
  getAll: () => api.get<SignalData[]>("/api/signals").then((r) => r.data),
  get: (code: string) => api.get<SignalData>(`/api/signals/${code}`).then((r) => r.data),
}
