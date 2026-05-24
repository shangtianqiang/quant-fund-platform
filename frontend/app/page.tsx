"use client"

import { useEffect, useState } from "react"
import { fundApi, strategyApi, signalApi, FundInfo, SignalData } from "@/lib/api"
import FundChart from "@/components/Charts/FundChart"
import PerfCard from "@/components/Cards/PerfCard"
import SignalPanel from "@/components/Signal/SignalPanel"

interface StrategySummary {
  name: string
  perf: { strategy_return: number; max_drawdown: number; sharpe_ratio: number; win_rate: number }
}

export default function DashboardPage() {
  const [funds, setFunds] = useState<FundInfo[]>([])
  const [chartData, setChartData] = useState<{ dates: string[]; funds: { name: string; nav: number[] }[] }>({
    dates: [],
    funds: [],
  })
  const [strategies, setStrategies] = useState<StrategySummary[]>([])
  const [signals, setSignals] = useState<SignalData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const fundList = await fundApi.list()
      setFunds(fundList)

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

      const stratList = await strategyApi.list()
      const stratResults = await Promise.all(
        stratList.map((s) =>
          strategyApi
            .run({ strategy_name: s.name, fund_code: "000217" })
            .catch(() => null)
        )
      )
      setStrategies(
        stratResults
          .filter((r): r is NonNullable<typeof r> => r !== null && r.type === "timing")
          .map((r) => ({
            name: r.strategy_name,
            perf: r.perf as StrategySummary["perf"],
          }))
      )

      const signalData = await signalApi.getAll()
      setSignals(signalData)
    } catch (e) {
      console.error("加载失败:", e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  const bestStrategy = strategies.reduce(
    (best, s) => (s.perf.strategy_return > (best?.perf.strategy_return ?? -Infinity) ? s : best),
    strategies[0]
  )

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-800">策略总览</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <PerfCard
          label="最佳策略"
          value={bestStrategy?.name || "-"}
          color="default"
        />
        <PerfCard
          label="策略收益"
          value={bestStrategy?.perf.strategy_return ?? "-"}
          suffix="%"
          color={(bestStrategy?.perf.strategy_return ?? 0) >= 0 ? "green" : "red"}
        />
        <PerfCard
          label="最大回撤"
          value={bestStrategy?.perf.max_drawdown ?? "-"}
          suffix="%"
          color="red"
        />
        <PerfCard
          label="夏普比率"
          value={bestStrategy?.perf.sharpe_ratio ?? "-"}
          color={(bestStrategy?.perf.sharpe_ratio ?? 0) >= 1 ? "green" : "default"}
        />
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
