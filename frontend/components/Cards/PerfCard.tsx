interface PerfCardProps {
  label: string
  value: string | number
  suffix?: string
  color?: "green" | "red" | "default"
}

export default function PerfCard({ label, value, suffix = "", color = "default" }: PerfCardProps) {
  const colorClass =
    color === "green" ? "text-green-600" : color === "red" ? "text-red-600" : "text-gray-900"

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${colorClass}`}>
        {value}
        {suffix && <span className="text-sm font-normal ml-0.5">{suffix}</span>}
      </div>
    </div>
  )
}
