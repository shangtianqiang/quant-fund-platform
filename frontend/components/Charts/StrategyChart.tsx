"use client"

import { useEffect, useRef } from "react"
import * as echarts from "echarts"

interface StrategyChartProps {
  dates: string[]
  nav: number[]
  equityCurve: number[]
  trades: { date: string; action: string; price: number }[]
  height?: string
}

export default function StrategyChart({ dates, nav, equityCurve, trades, height = "420px" }: StrategyChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    chartInstance.current = echarts.init(chartRef.current)

    const buyPoints = trades.filter((t) => t.action === "BUY").map((t) => [t.date, t.price])
    const sellPoints = trades.filter((t) => t.action === "SELL").map((t) => [t.date, t.price])

    const option: echarts.EChartsOption = {
      tooltip: { trigger: "axis" },
      legend: { data: ["单位净值", "策略净值", "买入", "卖出"], top: 5 },
      grid: { top: 40, bottom: 60, left: 60, right: 60 },
      dataZoom: [
        { type: "slider", start: 0, end: 100 },
        { type: "inside" },
      ],
      xAxis: { type: "category", data: dates },
      yAxis: [
        { type: "value", name: "净值", position: "left" },
        { type: "value", name: "策略净值", position: "right" },
      ],
      series: [
        {
          name: "单位净值",
          type: "line",
          data: nav,
          smooth: true,
          symbol: "none",
          lineStyle: { width: 1.5, color: "#333" },
          itemStyle: { color: "#333" },
        },
        {
          name: "策略净值",
          type: "line",
          data: equityCurve,
          smooth: true,
          symbol: "none",
          yAxisIndex: 1,
          lineStyle: { width: 2, color: "#c23531" },
          itemStyle: { color: "#c23531" },
          areaStyle: { opacity: 0.08, color: "#c23531" },
        },
        {
          name: "买入",
          type: "scatter",
          data: buyPoints,
          symbol: "triangle",
          symbolSize: 12,
          itemStyle: { color: "#f5222d" },
        },
        {
          name: "卖出",
          type: "scatter",
          data: sellPoints,
          symbol: "diamond",
          symbolSize: 12,
          itemStyle: { color: "#52c41a" },
        },
      ],
    }

    chartInstance.current.setOption(option)
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      chartInstance.current?.dispose()
    }
  }, [dates, nav, equityCurve, trades])

  return <div ref={chartRef} style={{ width: "100%", height }} />
}
