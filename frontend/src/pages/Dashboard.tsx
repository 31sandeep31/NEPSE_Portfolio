import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "../api/client"
import { fmtMoney, PriceCell } from "../components/PriceCell"
import { SignalBadge } from "../components/SignalBadge"
import { useUsername } from "../hooks/useUsername"

export function Dashboard() {
  const { username } = useUsername()
  const { data, isLoading, error } = useQuery({
    queryKey: ["analysis", username],
    queryFn: () => api.getAnalysis(username!),
    enabled: !!username,
    refetchInterval: 30_000,
  })

  if (!username) return null

  if (isLoading) return <p className="text-gray-500">Loading your portfolio...</p>
  if (error)
    return (
      <p className="text-red-600">
        Failed to load: {error instanceof Error ? error.message : "unknown"}
      </p>
    )
  if (!data) return null

  const noHoldings = data.holdings.length === 0
  const allSignals = data.holdings.flatMap((h) =>
    h.signals.map((s) => ({ ...s, symbol: h.symbol }))
  )

  return (
    <div className="space-y-6">
      <header className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">Hello, {username}</h1>
        <span
          className={`text-xs px-2 py-1 rounded ${
            data.market_open
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
              : "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-400"
          }`}
        >
          {data.market_open ? "Market open" : "Market closed"}
          {data.last_price_update &&
            ` · last update ${new Date(data.last_price_update).toLocaleTimeString()}`}
        </span>
      </header>

      {noHoldings ? (
        <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-3">
            Your portfolio is empty. Add a holding to get started.
          </p>
          <Link
            to="/portfolio"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go to Portfolio
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard label="Cost basis" value={`Rs ${fmtMoney(data.total_cost_basis)}`} />
            <StatCard label="Current value" value={`Rs ${fmtMoney(data.total_current_value)}`} />
            <StatCard
              label="Unrealized P&L"
              value={
                <PriceCell
                  value={data.total_unrealized_pl}
                  pct={data.total_unrealized_pl_pct}
                />
              }
            />
          </div>

          {allSignals.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-2">Active signals</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {allSignals.map((s, i) => (
                  <div key={i}>
                    <Link
                      to={`/stocks/${s.symbol}`}
                      className="text-sm font-mono text-blue-600 hover:underline"
                    >
                      {s.symbol}
                    </Link>
                    <SignalBadge signal={s} />
                  </div>
                ))}
              </div>
            </section>
          )}

          <section>
            <h2 className="text-lg font-semibold mb-2">Holdings</h2>
            <HoldingsTable analyses={data.holdings} />
          </section>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  )
}

function HoldingsTable({ analyses }: { analyses: import("../api/types").HoldingAnalysis[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr className="text-left">
            <th className="px-3 py-2">Symbol</th>
            <th className="px-3 py-2 text-right">Qty</th>
            <th className="px-3 py-2 text-right">Buy</th>
            <th className="px-3 py-2 text-right">LTP</th>
            <th className="px-3 py-2 text-right">Value</th>
            <th className="px-3 py-2 text-right">P&L</th>
            <th className="px-3 py-2 text-right">Signals</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((h) => (
            <tr key={h.holding_id} className="border-t border-gray-100 dark:border-gray-800">
              <td className="px-3 py-2 font-mono">
                <Link to={`/stocks/${h.symbol}`} className="text-blue-600 hover:underline">
                  {h.symbol}
                </Link>
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{h.qty}</td>
              <td className="px-3 py-2 text-right tabular-nums">{fmtMoney(h.buy_price)}</td>
              <td className="px-3 py-2 text-right">
                <PriceCell value={h.current_price} />
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{fmtMoney(h.current_value)}</td>
              <td className="px-3 py-2 text-right">
                <PriceCell value={h.unrealized_pl} pct={h.unrealized_pl_pct} />
              </td>
              <td className="px-3 py-2 text-right">{h.signals.length || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
