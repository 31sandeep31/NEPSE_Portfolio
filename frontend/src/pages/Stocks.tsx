import { useQuery } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../api/client"
import { PriceCell } from "../components/PriceCell"

export function Stocks() {
  const { data, isLoading } = useQuery({
    queryKey: ["stocks"],
    queryFn: () => api.listStocks(),
    refetchInterval: 30_000,
  })
  const [q, setQ] = useState("")

  const filtered = useMemo(() => {
    if (!data) return []
    const needle = q.trim().toUpperCase()
    if (!needle) return data
    return data.filter((s) => s.symbol.toUpperCase().includes(needle))
  }, [data, q])

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">All stocks</h1>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search symbol..."
          className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded w-64"
        />
      </div>
      {isLoading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr className="text-left">
                <th className="px-3 py-2">Symbol</th>
                <th className="px-3 py-2 text-right">LTP</th>
                <th className="px-3 py-2 text-right">Open</th>
                <th className="px-3 py-2 text-right">High</th>
                <th className="px-3 py-2 text-right">Low</th>
                <th className="px-3 py-2 text-right">Qty</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 200).map((s) => (
                <tr key={s.symbol} className="border-t border-gray-100 dark:border-gray-800">
                  <td className="px-3 py-2 font-mono">
                    <Link to={`/stocks/${s.symbol}`} className="text-blue-600 hover:underline">
                      {s.symbol}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <PriceCell value={s.ltp} pct={s.pct_change} />
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{s.open?.toFixed(2) ?? "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{s.high?.toFixed(2) ?? "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{s.low?.toFixed(2) ?? "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{s.qty ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length > 200 && (
            <p className="text-xs text-gray-500 px-3 py-2">
              Showing first 200 of {filtered.length}. Filter to narrow.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
