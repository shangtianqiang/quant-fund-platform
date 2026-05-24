import { SignalData } from "@/lib/api"

interface SignalPanelProps {
  signals: SignalData[]
}

export default function SignalPanel({ signals }: SignalPanelProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {signals.map((s) => (
        <div key={s.code} className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
          <h4 className="text-sm font-semibold mb-3 text-gray-800">
            {s.name}
            <span className="text-xs text-gray-400 ml-1">({s.code})</span>
          </h4>
          <div className="space-y-2 text-xs">
            <Row label="最新净值" value={s.nav.toFixed(4)} />
            <Row
              label="趋势"
              value={s.trend}
              badge={s.trend === "上升" ? "green" : "red"}
            />
            <Row label="RSI(6/14)" value={`${s.rsi6 ?? "-"} / ${s.rsi14 ?? "-"}`} />
            <Row label="MA5/20/60" value={`${s.ma5 ?? "-"} / ${s.ma20 ?? "-"} / ${s.ma60 ?? "-"}`} />
            <Row label="回撤" value={`${s.drawdown}%`} className="text-red-600" />
            <Row label="动量(20日)" value={s.momentum != null ? `${s.momentum}%` : "-"} />
          </div>
        </div>
      ))}
    </div>
  )
}

function Row({
  label,
  value,
  badge,
  className = "",
}: {
  label: string
  value: string | number
  badge?: "green" | "red"
  className?: string
}) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-500">{label}</span>
      {badge ? (
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            badge === "green" ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"
          }`}
        >
          {value}
        </span>
      ) : (
        <span className={`font-medium ${className}`}>{value}</span>
      )}
    </div>
  )
}
