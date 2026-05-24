"use client"

import { useEffect, useState } from "react"
import { fundApi, FundInfo, FundNavResponse } from "@/lib/api"
import FundChart from "@/components/Charts/FundChart"

export default function FundsPage() {
  const [funds, setFunds] = useState<FundInfo[]>([])
  const [selectedCode, setSelectedCode] = useState("")
  const [fundData, setFundData] = useState<FundNavResponse | null>(null)
  const [allNavData, setAllNavData] = useState<{ dates: string[]; funds: { name: string; nav: number[] }[] }>({
    dates: [],
    funds: [],
  })
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fundApi.list().then(async (fundList) => {
      setFunds(fundList)
      if (fundList.length > 0) {
        setSelectedCode(fundList[0].code)
      }

      const results = await Promise.all(fundList.map((f) => fundApi.getNav(f.code).catch(() => null)))
      const valid = results.filter(Boolean)
      if (valid.length > 0) {
        setAllNavData({
          dates: valid[0]!.data.map((d) => d.date),
          funds: valid.map((r, i) => ({
            name: fundList[i].name,
            nav: r!.data.map((d) => d.nav),
          })),
        })
      }
    })
  }, [])

  useEffect(() => {
    if (!selectedCode) return
    setLoading(true)
    fundApi
      .getNav(selectedCode)
      .then(setFundData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedCode])

  async function handleRefresh() {
    if (!selectedCode) return
    setRefreshing(true)
    try {
      await fundApi.refresh(selectedCode)
      const data = await fundApi.getNav(selectedCode)
      setFundData(data)
    } catch (e) {
      console.error(e)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">基金管理</h1>
        <div className="flex items-center gap-3">
          <select
            value={selectedCode}
            onChange={(e) => setSelectedCode(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {funds.map((f) => (
              <option key={f.code} value={f.code}>
                {f.name} ({f.code})
              </option>
            ))}
          </select>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {refreshing ? "刷新中..." : "刷新数据"}
          </button>
        </div>
      </div>

      {fundData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">最新净值</div>
            <div className="text-2xl font-bold">{fundData.latest_nav}</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">半年涨幅</div>
            <div
              className={`text-2xl font-bold ${
                (fundData.half_year_return ?? 0) >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {fundData.half_year_return}%
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">数据条数</div>
            <div className="text-2xl font-bold">{fundData.data.length}</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">数据区间</div>
            <div className="text-sm font-medium">
              {fundData.data[0]?.date} ~ {fundData.data[fundData.data.length - 1]?.date}
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold mb-3 text-gray-700">四只基金净值对比</h2>
        <FundChart dates={allNavData.dates} funds={allNavData.funds} />
      </div>

      {fundData && (
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
          <h2 className="text-sm font-semibold mb-3 text-gray-700">
            {fundData.fund?.name} 净值走势
          </h2>
          <FundChart
            dates={fundData.data.map((d) => d.date)}
            funds={[{ name: fundData.fund?.name || "", nav: fundData.data.map((d) => d.nav) }]}
          />
        </div>
      )}
    </div>
  )
}
