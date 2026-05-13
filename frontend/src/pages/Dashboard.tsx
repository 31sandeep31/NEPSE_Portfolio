import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "../api/client"
import type { HoldingAnalysis, HoldingInput } from "../api/types"
import { MoversStrip } from "../components/MoversStrip"
import { fmtMoney, PriceCell } from "../components/PriceCell"
import { SignalBadge } from "../components/SignalBadge"
import { usePortfolio } from "../hooks/usePortfolio"

export function Dashboard() {
  const { holdings } = usePortfolio()
  const payload: HoldingInput[] = holdings.map((h) => ({
    client_id: h.client_id,
    symbol: h.symbol,
    qty: h.qty,
    buy_price: h.buy_price,
    buy_date: new Date(h.buy_date).toISOString(),
    target_pct: h.target_pct ?? null,
  }))

  const { data, isLoading, error } = useQuery({
    queryKey: ["analysis", JSON.stringify(payload)],
    queryFn: () => api.postAnalysis(payload),
    enabled: holdings.length > 0,
    refetchInterval: 30_000,
  })

  const noHoldings = holdings.length === 0

  return (
    <div className="space-y-6">
      <header className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        {data && (
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
        )}
      </header>

      {noHoldings ? (
        <>
          <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-3">
              Your portfolio is empty. Add a holding to get started.
              <br />
              <span className="text-xs">Saved only in this browser — no account, no login.</span>
            </p>
            <Link
              to="/portfolio"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Go to Portfolio
            </Link>
          </div>
          <section>
            <h2 className="text-lg font-semibold mb-2">Market today</h2>
            <MoversStrip />
          </section>
        </>
      ) : isLoading ? (
        <p className="text-gray-500">Loading your portfolio...</p>
      ) : error ? (
        <p className="text-red-600">
          Failed to load: {error instanceof Error ? error.message : "unknown"}
        </p>
      ) : !data ? null : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard
              label="Cost basis"
              value={`Rs ${fmtMoney(data.total_cost_basis_with_fees)}`}
              sub="incl. buy fees"
            />
            <StatCard label="Current value" value={`Rs ${fmtMoney(data.total_current_value)}`} />
            <StatCard
              label="Gross P&L"
              value={
                <PriceCell value={data.total_unrealized_pl} pct={data.total_unrealized_pl_pct} />
              }
              sub="price change only"
            />
            <StatCard
              label="Net if sold now"
              value={
                <PriceCell
                  value={data.total_net_pl_if_sold}
                  pct={data.total_net_pl_pct_if_sold}
                />
              }
              sub="after broker, SEBON, DP, CGT"
            />
          </div>

          <section>
            <h2 className="text-lg font-semibold mb-2">Market today</h2>
            <MoversStrip />
          </section>

          {data.holdings.some((h) => h.signals.length > 0) && (
            <section>
              <h2 className="text-lg font-semibold mb-2">Active signals</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {data.holdings.flatMap((h) =>
                  h.signals.map((s, i) => (
                    <div key={`${h.client_id ?? h.symbol}-${i}`}>
                      <Link
                        to={`/stocks/${h.symbol}`}
                        className="text-sm font-mono text-blue-600 hover:underline"
                      >
                        {h.symbol}
                      </Link>
                      <SignalBadge signal={s} />
                    </div>
                  )),
                )}
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

function StatCard({
  label,
  value,
  sub,
}: {
  label: string
  value: React.ReactNode
  sub?: string
}) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-1">{sub}</div>}
    </div>
  )
}

function HoldingsTable({ analyses }: { analyses: HoldingAnalysis[] }) {
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
            <th className="px-3 py-2 text-right">Gross P&L</th>
            <th className="px-3 py-2 text-right" title="After broker, SEBON, DP, CGT">
              Net P&L
            </th>
            <th className="px-3 py-2 text-right">Signals</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((h) => (
            <tr
              key={h.client_id ?? h.symbol}
              className="border-t border-gray-100 dark:border-gray-800"
            >
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
              <td
                className="px-3 py-2 text-right"
                title={
                  h.sell_fees
                    ? `Broker ${h.sell_fees.broker_commission.toFixed(2)} · SEBON ${h.sell_fees.sebon_levy.toFixed(2)} · DP ${h.sell_fees.dp_charge.toFixed(2)} · CGT ${h.sell_fees.capital_gains_tax.toFixed(2)} @ ${(h.sell_fees.cgt_rate * 100).toFixed(1)}%`
                    : undefined
                }
              >
                <PriceCell value={h.net_pl_if_sold} pct={h.net_pl_pct_if_sold} />
              </td>
              <td className="px-3 py-2 text-right">{h.signals.length || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
