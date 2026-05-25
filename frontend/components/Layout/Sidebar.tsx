"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { href: "/", label: "策略总览", icon: " " },
  { href: "/funds", label: "基金管理", icon: " " },
  { href: "/strategies", label: "策略回测", icon: " " },
  { href: "/signals", label: "信号监控", icon: " " },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-5 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-800">量化投资平台</h1>
        <p className="text-xs text-gray-400 mt-1">Quant Fund Dashboard</p>
      </div>
      <nav className="flex-1 p-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg mb-1 text-sm transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-600 font-medium"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-gray-200 text-xs text-gray-400">
        v1.0.0
      </div>
    </aside>
  )
}
