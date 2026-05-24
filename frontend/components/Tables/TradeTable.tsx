import { TradeRecord } from "@/lib/api"

interface TradeTableProps {
  trades: TradeRecord[]
}

export default function TradeTable({ trades }: TradeTableProps) {
  if (!trades.length) {
    return <p className="text-gray-400 text-sm p-4">无交易记录</p>
  }

  return (
    <div className="overflow-auto max-h-80">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-gray-600">日期</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">操作</th>
            <th className="text-right px-4 py-2 font-medium text-gray-600">价格</th>
            <th className="text-right px-4 py-2 font-medium text-gray-600">份额</th>
            <th className="text-right px-4 py-2 font-medium text-gray-600">金额</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i} className="border-t border-gray-100">
              <td className="px-4 py-2">{t.date}</td>
              <td className={`px-4 py-2 font-medium ${t.action === "BUY" ? "text-red-600" : "text-green-600"}`}>
                {t.action === "BUY" ? "买入" : "卖出"}
              </td>
              <td className="px-4 py-2 text-right">{t.price.toFixed(4)}</td>
              <td className="px-4 py-2 text-right">{t.shares?.toFixed(2) || "-"}</td>
              <td className="px-4 py-2 text-right">{t.amount?.toFixed(2) || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
