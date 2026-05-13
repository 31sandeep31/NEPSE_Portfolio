import { useQuery } from "@tanstack/react-query"
import {
  Area,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { api } from "../api/client"

interface Props {
  symbol: string
  days?: number
  buyPrice?: number | null
  high52w?: number | null
  low52w?: number | null
}

export function PriceChart({ symbol, days = 90, buyPrice, high52w, low52w }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["history", symbol, days],
    queryFn: () => api.getStockHistory(symbol, days),
  })

  if (isLoading) return <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading chart...</div>
  if (error)
    return (
      <div className="h-64 flex items-center justify-center text-red-500 text-sm">
        {error instanceof Error ? error.message : "Failed to load history"}
      </div>
    )
  if (!data || data.length === 0)
    return (
      <div className="h-64 flex items-center justify-center text-gray-400 text-sm text-center px-4">
        History is still being collected. Check back in a few minutes after the daily backfill runs.
      </div>
    )

  const chartData = data
    .filter((b) => b.close != null)
    .map((b) => ({
      date: b.date,
      close: b.close,
      high: b.high,
      low: b.low,
    }))

  const closes = chartData.map((b) => b.close as number)
  const dataMin = Math.min(...closes)
  const dataMax = Math.max(...closes)
  const pad = (dataMax - dataMin) * 0.1 || 1
  const yMin = Math.floor(dataMin - pad)
  const yMax = Math.ceil(dataMax + pad)

  return (
    <div className="w-full h-72">
      <ResponsiveContainer>
        <ComposedChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="closeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2563eb" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(d) => d.slice(5)}
            interval="preserveStartEnd"
            minTickGap={40}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v) => v.toFixed(0)}
            width={48}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(17, 24, 39, 0.95)",
              border: "1px solid #374151",
              borderRadius: 6,
              fontSize: 12,
              color: "#e5e7eb",
            }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(v) => (typeof v === "number" ? v.toFixed(2) : String(v))}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke="#2563eb"
            strokeWidth={2}
            fill="url(#closeFill)"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke="#9ca3af"
            strokeDasharray="2 4"
            strokeWidth={1}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#9ca3af"
            strokeDasharray="2 4"
            strokeWidth={1}
            dot={false}
          />
          {buyPrice != null && (
            <ReferenceLine
              y={buyPrice}
              stroke="#10b981"
              strokeDasharray="4 2"
              label={{ value: `Buy ${buyPrice.toFixed(2)}`, fill: "#10b981", fontSize: 11, position: "left" }}
            />
          )}
          {high52w != null && (
            <ReferenceLine y={high52w} stroke="#ef4444" strokeDasharray="1 4" />
          )}
          {low52w != null && (
            <ReferenceLine y={low52w} stroke="#ef4444" strokeDasharray="1 4" />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
