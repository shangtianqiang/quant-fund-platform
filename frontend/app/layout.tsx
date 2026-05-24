import type { Metadata } from "next"
import { Geist } from "next/font/google"
import "./globals.css"
import Sidebar from "@/components/Layout/Sidebar"

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })

export const metadata: Metadata = {
  title: "黄金ETF量化投资平台",
  description: "基金量化策略分析、回测与信号监控",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${geist.variable} h-full`}>
      <body className="min-h-full flex bg-gray-50 text-gray-900">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="p-6">{children}</div>
        </main>
      </body>
    </html>
  )
}
