"use client"

import { useEffect, useState } from "react"
import { fundApi, strategyApi, signalApi, FundInfo, SignalData, BacktestResult } from "@/lib/api"
import FundChart from "@/components/Charts/FundChart"
import PerfCard from "@/components/Cards/PerfCard"
import SignalPanel from "@/components/Signal/SignalPanel"

export default function DashboardPage() {
  const [funds, setFunds] = useState<FundInfo[]>([])
  const [chartData, setChartData] = useState<{ dates: string[]; funds: { name: string; nav: number[] }[] }>({
    dates: [],
    funds: [],
  })
  const [signals, setSignals] = useState<SignalData[]>([])
  const [bestResult, setBestResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisFund, setAnalysisFund] = useState("")

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [fundList, signalData] = await Promise.all([fundApi.list(), signalApi.getAll()])
      setFunds(fundList)
      setSignals(signalData)
      if (fundList.length > 0) {
        setAnalysisFund(fundList[0].code)
      }

      const navResults = await Promise.all(fundList.map((f) => fundApi.getNav(f.code).catch(() => null)))
      const validResults = navResults.filter(Boolean)
      if (validResults.length > 0) {
        setChartData({
          dates: validResults[0]!.data.map((d) => d.date),
          funds: validResults.map((r, i) => ({
            name: fundList[i].name,
            nav: r!.data.map((d) => d.nav),
          })),
        })
      }
    } catch (e) {
      console.error("加载失败:", e)
    } finally {
      setLoading(false)
    }
  }

  async function runAnalysis() {
    if (!analysisFund) return
    setAnalyzing(true)
    setBestResult(null)
    try {
      const stratList = await strategyApi.list()
      const results = await Promise.all(
        stratList.map((s) =>
          strategyApi
            .run({ strategy_name: s.name, fund_code: analysisFund })
            .catch(() => null)
        )
      )
      const timingResults = results.filter(
        (r): r is NonNullable<typeof r> => r !== null && r.type === "timing"
      )
      if (timingResults.length > 0) {
        const best = timingResults.reduce((a, b) =>
          (a.perf as { strategy_return: number }).strategy_return >
          (b.perf as { strategy_return: number }).strategy_return
            ? a
            : b
        )
        setBestResult(best)
      }
    } catch (e) {
      console.error("策略分析失败:", e)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  const perf = bestResult?.perf as { strategy_return: number; max_drawdown: number; sharpe_ratio: number } | undefined

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-800">策略总览</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <PerfCard label="最佳策略" value={bestResult?.strategy_name || "点击下方分析"} color="default" />
        <PerfCard
          label="策略收益"
          value={perf?.strategy_return ?? "-"}
          suffix="%"
          color={perf ? (perf.strategy_return >= 0 ? "green" : "red") : "default"}
        />
        <PerfCard
          label="最大回撤"
          value={perf?.max_drawdown ?? "-"}
          suffix="%"
          color="red"
        />
        <PerfCard
          label="夏普比率"
          value={perf?.sharpe_ratio ?? "-"}
          color={perf ? (perf.sharpe_ratio >= 1 ? "green" : "default") : "default"}
        />
      </div>

      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-sm text-gray-600">选择基金：</span>
          <select
            value={analysisFund}
            onChange={(e) => setAnalysisFund(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
          >
            {funds.map((f) => (
              <option key={f.code} value={f.code}>{f.name} ({f.code})</option>
            ))}
          </select>
          <button
            onClick={runAnalysis}
            disabled={analyzing || !analysisFund}
            className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? "分析中..." : "运行策略分析"}
          </button>
        </div>
        <p className="text-xs text-gray-400">对选中的基金运行全部策略，找出最佳策略推荐</p>
      </div>

      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold mb-3 text-gray-700">基金净值走势</h2>
        <FundChart dates={chartData.dates} funds={chartData.funds} />
      </div>

      <div>
        <h2 className="text-sm font-semibold mb-3 text-gray-700">最新市场信号</h2>
        <SignalPanel signals={signals} />
      </div>
    </div>
  )
}
