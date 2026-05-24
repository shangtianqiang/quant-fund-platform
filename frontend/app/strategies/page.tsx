"use client"

import { useEffect, useState } from "react"
import { strategyApi, fundApi, StrategyInfo, FundInfo, BacktestResult } from "@/lib/api"
import StrategyChart from "@/components/Charts/StrategyChart"
import PerfCard from "@/components/Cards/PerfCard"
import TradeTable from "@/components/Tables/TradeTable"

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<StrategyInfo[]>([])
  const [funds, setFunds] = useState<FundInfo[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState("")
  const [selectedFund, setSelectedFund] = useState("000217")
  const [capital, setCapital] = useState(100000)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    Promise.all([strategyApi.list(), fundApi.list()]).then(([s, f]) => {
      setStrategies(s)
      setFunds(f)
      if (s.length > 0) setSelectedStrategy(s[0].name)
    })
  }, [])

  async function handleRun() {
    if (!selectedStrategy) return
    setLoading(true)
    try {
      const res = await strategyApi.run({
        strategy_name: selectedStrategy,
        fund_code: selectedFund,
        initial_capital: capital,
      })
      setResult(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const isDca = result?.type === "dca"
  const perf = result?.perf

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-800">策略回测</h1>

      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">策略</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              {strategies.map((s) => (
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">基金</label>
            <select
              value={selectedFund}
              onChange={(e) => setSelectedFund(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              {funds.map((f) => (
                <option key={f.code} value={f.code}>{f.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">初始资金</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-32"
            />
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "运行中..." : "运行回测"}
          </button>
        </div>
        {strategies.find((s) => s.name === selectedStrategy) && (
          <p className="text-xs text-gray-400 mt-2">
            {strategies.find((s) => s.name === selectedStrategy)?.description}
          </p>
        )}
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {isDca ? (
              <>
                <PerfCard label="总投入" value={(perf as { total_invested: number }).total_invested} suffix="元" />
                <PerfCard
                  label="当前市值"
                  value={(perf as { dca_value: number }).dca_value}
                  suffix="元"
                  color={(perf as { dca_return: number }).dca_return >= 0 ? "green" : "red"}
                />
                <PerfCard
                  label="定投收益"
                  value={(perf as { dca_return: number }).dca_return}
                  suffix="%"
                  color={(perf as { dca_return: number }).dca_return >= 0 ? "green" : "red"}
                />
              </>
            ) : (
              <>
                <PerfCard
                  label="策略收益"
                  value={(perf as { strategy_return: number }).strategy_return}
                  suffix="%"
                  color={(perf as { strategy_return: number }).strategy_return >= 0 ? "green" : "red"}
                />
                <PerfCard
                  label="基准收益"
                  value={(perf as { benchmark_return: number }).benchmark_return}
                  suffix="%"
                  color={(perf as { benchmark_return: number }).benchmark_return >= 0 ? "green" : "red"}
                />
                <PerfCard
                  label="最大回撤"
                  value={(perf as { max_drawdown: number }).max_drawdown}
                  suffix="%"
                  color="red"
                />
                <PerfCard
                  label="夏普比率"
                  value={(perf as { sharpe_ratio: number }).sharpe_ratio}
                  color={(perf as { sharpe_ratio: number }).sharpe_ratio >= 1 ? "green" : "default"}
                />
                <PerfCard
                  label="年化收益"
                  value={(perf as { annual_return: number }).annual_return}
                  suffix="%"
                  color={(perf as { annual_return: number }).annual_return >= 0 ? "green" : "red"}
                />
                <PerfCard
                  label="胜率"
                  value={(perf as { win_rate: number }).win_rate}
                  suffix="%"
                  color={(perf as { win_rate: number }).win_rate >= 50 ? "green" : "red"}
                />
                <PerfCard label="交易次数" value={(perf as { trade_count: number }).trade_count} />
              </>
            )}
          </div>

          {isDca ? (
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <h3 className="text-sm font-semibold mb-3 text-gray-700">定投曲线</h3>
              <StrategyChart
                dates={result.dates}
                nav={result.nav}
                equityCurve={result.value_curve || []}
                trades={[]}
              />
            </div>
          ) : (
            <>
              <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
                <h3 className="text-sm font-semibold mb-3 text-gray-700">净值曲线 & 买卖信号</h3>
                <StrategyChart
                  dates={result.dates}
                  nav={result.nav}
                  equityCurve={result.equity_curve || []}
                  trades={result.trades}
                />
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
                <h3 className="text-sm font-semibold mb-3 text-gray-700">交易记录</h3>
                <TradeTable trades={result.trades} />
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
