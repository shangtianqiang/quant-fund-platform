"use client"

import { useEffect, useState } from "react"
import { fundApi, FundInfo, FundNavResponse, FUND_TYPES, clearCache } from "@/lib/api"
import FundChart from "@/components/Charts/FundChart"
import { LoadingSpinner, ErrorMessage } from "@/components/UI/StatusMessage"

export default function FundsPage() {
  const [funds, setFunds] = useState<FundInfo[]>([])
  const [selectedCode, setSelectedCode] = useState("")
  const [fundData, setFundData] = useState<FundNavResponse | null>(null)
  const [allNavData, setAllNavData] = useState<{ dates: string[]; funds: { name: string; nav: number[] }[] }>({
    dates: [],
    funds: [],
  })
  const [loading, setLoading] = useState(true)
  const [fundLoading, setFundLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState("")
  const [filterType, setFilterType] = useState("全部")

  // 添加基金表单
  const [showForm, setShowForm] = useState(false)
  const [formCode, setFormCode] = useState("")
  const [formName, setFormName] = useState("")
  const [formType, setFormType] = useState("其他")
  const [adding, setAdding] = useState(false)
  const [formError, setFormError] = useState("")

  // 编辑状态
  const [editingCode, setEditingCode] = useState("")
  const [editName, setEditName] = useState("")
  const [editType, setEditType] = useState("")

  useEffect(() => {
    loadFunds()
  }, [])

  async function loadFunds() {
    setLoading(true)
    setError("")
    try {
      const fundList = await fundApi.list()
      setFunds(fundList)
      if (fundList.length > 0 && !selectedCode) {
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
    } catch (e) {
      console.error(e)
      setError("加载基金数据失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!selectedCode) return
    setFundLoading(true)
    fundApi
      .getNav(selectedCode)
      .then(setFundData)
      .catch(console.error)
      .finally(() => setFundLoading(false))
  }, [selectedCode])

  async function handleRefresh() {
    if (!selectedCode) return
    setRefreshing(true)
    try {
      await fundApi.refresh(selectedCode)
      clearCache("funds:list")
      const data = await fundApi.getNav(selectedCode)
      setFundData(data)
    } catch (e) {
      console.error(e)
    } finally {
      setRefreshing(false)
    }
  }

  async function handleAdd() {
    if (!formCode || !formName) {
      setFormError("请填写基金代码和名称")
      return
    }
    setAdding(true)
    setFormError("")
    try {
      await fundApi.create({ code: formCode, name: formName, fund_type: formType })
      setShowForm(false)
      setFormCode("")
      setFormName("")
      setFormType("其他")
      await loadFunds()
    } catch (e: unknown) {
      const msg = e instanceof Error && "response" in e ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail : "添加失败"
      setFormError(msg || "添加失败")
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(code: string, name: string) {
    if (!confirm(`确定删除 "${name}" 吗？相关的净值数据也会被删除。`)) return
    try {
      await fundApi.delete(code)
      if (selectedCode === code) {
        setSelectedCode("")
        setFundData(null)
      }
      await loadFunds()
    } catch (e) {
      console.error(e)
    }
  }

  function startEdit(fund: FundInfo) {
    setEditingCode(fund.code)
    setEditName(fund.name)
    setEditType(fund.fund_type)
  }

  async function handleSaveEdit() {
    try {
      await fundApi.update(editingCode, { name: editName, fund_type: editType })
      setEditingCode("")
      await loadFunds()
    } catch (e) {
      console.error(e)
    }
  }

  const filteredFunds = filterType === "全部" ? funds : funds.filter((f) => f.fund_type === filterType)
  const usedTypes = [...new Set(funds.map((f) => f.fund_type))]

  if (loading) return <LoadingSpinner text="加载基金数据..." />
  if (error) return <ErrorMessage text={error} onRetry={loadFunds} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">基金管理</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          {showForm ? "取消" : "+ 添加基金"}
        </button>
      </div>

      {/* 添加基金表单 */}
      {showForm && (
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
          <h2 className="text-sm font-semibold mb-3 text-gray-700">添加新基金</h2>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">基金代码</label>
              <input
                value={formCode}
                onChange={(e) => setFormCode(e.target.value)}
                placeholder="如 519736"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-32"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">基金名称</label>
              <input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="如 交银定期支付双息平衡混合"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg w-48"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">基金类型</label>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                {FUND_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <button
              onClick={handleAdd}
              disabled={adding}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {adding ? "添加中..." : "确认添加"}
            </button>
          </div>
          {formError && <p className="text-xs text-red-500 mt-2">{formError}</p>}
          <p className="text-xs text-gray-400 mt-2">添加后会自动从天天基金拉取最近半年的净值数据</p>
        </div>
      )}

      {/* 类型筛选 */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-gray-500">类型筛选：</span>
        {["全部", ...usedTypes].map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`px-3 py-1 text-xs rounded-full transition-colors ${
              filterType === t ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* 基金列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3 font-medium">代码</th>
              <th className="text-left px-4 py-3 font-medium">名称</th>
              <th className="text-left px-4 py-3 font-medium">类型</th>
              <th className="text-right px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredFunds.map((fund) => (
              <tr key={fund.code} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-800">{fund.code}</td>
                <td className="px-4 py-3">
                  {editingCode === fund.code ? (
                    <input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="px-2 py-1 text-sm border border-gray-300 rounded w-48"
                    />
                  ) : (
                    <span className="text-gray-800">{fund.name}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {editingCode === fund.code ? (
                    <select
                      value={editType}
                      onChange={(e) => setEditType(e.target.value)}
                      className="px-2 py-1 text-sm border border-gray-300 rounded bg-white"
                    >
                      {FUND_TYPES.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-600">{fund.fund_type}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {editingCode === fund.code ? (
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={handleSaveEdit} className="text-xs text-green-600 hover:underline">保存</button>
                      <button onClick={() => setEditingCode("")} className="text-xs text-gray-400 hover:underline">取消</button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-end gap-3">
                      <button
                        onClick={() => setSelectedCode(fund.code)}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        详情
                      </button>
                      <button
                        onClick={() => startEdit(fund)}
                        className="text-xs text-gray-500 hover:underline"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDelete(fund.code, fund.name)}
                        className="text-xs text-red-500 hover:underline"
                      >
                        删除
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {filteredFunds.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">
                  暂无基金，点击上方"添加基金"按钮添加
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 基金详情 */}
      {fundLoading ? (
        <LoadingSpinner text="加载基金详情..." />
      ) : fundData ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">最新净值</div>
            <div className="text-2xl font-bold">{fundData.latest_nav}</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-xs text-gray-500 mb-1">半年涨幅</div>
            <div className={`text-2xl font-bold ${(fundData.half_year_return ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
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
      ) : null}

      {/* 净值对比图 */}
      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold mb-3 text-gray-700">
          {funds.length}只基金净值对比
        </h2>
        <FundChart dates={allNavData.dates} funds={allNavData.funds} />
      </div>

      {/* 单只基金图表 */}
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
