import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "../api/client"
import type { MoverRow } from "../api/types"

export function MoversStrip() {
  const { data, isLoading } = useQuery({
    queryKey: ["movers"],
    queryFn: () => api.getMovers(5),
    refetchInterval: 30_000,
  })

  if (isLoading || !data) return null

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <MoverColumn title="Top gainers" rows={data.gainers} />
        <MoverColumn title="Top losers" rows={data.losers} />
        <MoverColumn title="Most active" rows={data.by_volume} showVol />
      </div>
      {data.sector_summary.length > 0 && (
        <SectorHeatmap rows={data.sector_summary} />
      )}
    </div>
  )
}

function MoverColumn({
  title,
  rows,
  showVol,
}: {
  title: string
  rows: MoverRow[]
  showVol?: boolean
}) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
      <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">{title}</div>
      <ul className="space-y-1">
        {rows.map((r) => (
          <li key={r.symbol} className="flex items-center justify-between text-sm">
            <Link
              to={`/stocks/${r.symbol}`}
              className="font-mono text-blue-600 hover:underline"
            >
              {r.symbol}
            </Link>
            <div className="flex items-center gap-3 tabular-nums">
              <span className="text-gray-600 dark:text-gray-400 text-xs">
                {r.ltp?.toFixed(2) ?? "—"}
              </span>
              {showVol ? (
                <span className="text-xs text-gray-500">
                  {r.qty != null ? (r.qty >= 1000 ? `${(r.qty / 1000).toFixed(1)}k` : r.qty) : "—"}
                </span>
              ) : (
                <span
                  className={`text-xs font-medium ${
                    (r.pct_change ?? 0) > 0
                      ? "text-green-600 dark:text-green-400"
                      : (r.pct_change ?? 0) < 0
                        ? "text-red-600 dark:text-red-400"
                        : ""
                  }`}
                >
                  {r.pct_change != null
                    ? `${r.pct_change > 0 ? "+" : ""}${r.pct_change.toFixed(2)}%`
                    : "—"}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SectorHeatmap({ rows }: { rows: { sector: string; avg_pct_change: number; up: number; down: number; count: number }[] }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
      <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">Sectors</div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {rows.map((r) => {
          const bg = bgForPct(r.avg_pct_change)
          return (
            <div
              key={r.sector}
              className={`rounded p-2 text-xs ${bg}`}
              title={`${r.up} up, ${r.down} down (of ${r.count})`}
            >
              <div className="font-medium truncate">{r.sector}</div>
              <div className="flex items-center justify-between mt-1 tabular-nums">
                <span>
                  {r.avg_pct_change > 0 ? "+" : ""}
                  {r.avg_pct_change.toFixed(2)}%
                </span>
                <span className="text-[10px] opacity-70">{r.up}/{r.count}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function bgForPct(p: number): string {
  if (p > 2) return "bg-green-200 text-green-900 dark:bg-green-900/60 dark:text-green-200"
  if (p > 0.5) return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
  if (p > -0.5) return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
  if (p > -2) return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
  return "bg-red-200 text-red-900 dark:bg-red-900/60 dark:text-red-200"
}
