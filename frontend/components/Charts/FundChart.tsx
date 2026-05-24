"use client"

import { useEffect, useRef } from "react"
import * as echarts from "echarts"

interface FundChartProps {
  dates: string[]
  funds: { name: string; nav: number[] }[]
  height?: string
}

export default function FundChart({ dates, funds, height = "400px" }: FundChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    chartInstance.current = echarts.init(chartRef.current)

    const option: echarts.EChartsOption = {
      tooltip: { trigger: "axis" },
      legend: { top: 5 },
      grid: { top: 40, bottom: 60, left: 60, right: 20 },
      dataZoom: [
        { type: "slider", start: 0, end: 100 },
        { type: "inside" },
      ],
      xAxis: { type: "category", data: dates },
      yAxis: { type: "value", name: "单位净值" },
      series: funds.map((f) => ({
        name: f.name,
        type: "line" as const,
        data: f.nav,
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2 },
      })),
    }

    chartInstance.current.setOption(option)
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      chartInstance.current?.dispose()
    }
  }, [dates, funds])

  return <div ref={chartRef} style={{ width: "100%", height }} />
}
