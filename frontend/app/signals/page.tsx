"use client"

import { useEffect, useState } from "react"
import { signalApi, SignalData, clearCache } from "@/lib/api"
import SignalPanel from "@/components/Signal/SignalPanel"
import { LoadingSpinner, ErrorMessage } from "@/components/UI/StatusMessage"

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    loadSignals()
  }, [])

  async function loadSignals() {
    setLoading(true)
    setError("")
    try {
      const data = await signalApi.getAll()
      setSignals(data)
    } catch (e) {
      console.error(e)
      setError("加载信号数据失败")
    } finally {
      setLoading(false)
    }
  }

  function refresh() {
    clearCache("signals:all")
    loadSignals()
  }

  if (loading) return <LoadingSpinner text="加载信号数据..." />
  if (error) return <ErrorMessage text={error} onRetry={loadSignals} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">信号监控</h1>
        <button onClick={refresh} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          刷新信号
        </button>
      </div>

      <SignalPanel signals={signals} />

      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold mb-3 text-gray-700">信号说明</h2>
        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>趋势</strong>：MA20 &gt; MA60 为上升趋势，反之为下降趋势</p>
          <p><strong>RSI</strong>：&lt;30 超卖（买入机会），&gt;70 超买（卖出信号）</p>
          <p><strong>回撤</strong>：从历史最高净值的跌幅，超过-10%需警惕</p>
          <p><strong>动量</strong>：20日涨跌幅，正值表示短期向上动能</p>
        </div>
      </div>
    </div>
  )
}
