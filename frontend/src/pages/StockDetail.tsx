import { useQuery } from "@tanstack/react-query"
import { useParams } from "react-router-dom"
import { api } from "../api/client"
import { fmtMoney, PriceCell } from "../components/PriceCell"

export function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>()
  const { data, isLoading, error } = useQuery({
    queryKey: ["stock", symbol],
    queryFn: () => api.getStock(symbol!),
    enabled: !!symbol,
    refetchInterval: 30_000,
  })

  if (isLoading) return <p className="text-gray-500">Loading {symbol}...</p>
  if (error)
    return <p className="text-red-600">Failed: {error instanceof Error ? error.message : ""}</p>
  if (!data) return null

  const { live, fundamentals: f } = data

  let pricePos: number | null = null
  if (f?.week_52_high && f?.week_52_low && live.ltp != null) {
    const span = f.week_52_high - f.week_52_low
    pricePos = span > 0 ? ((live.ltp - f.week_52_low) / span) * 100 : 50
  }

  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1 className="text-3xl font-mono font-bold">{live.symbol}</h1>
          {live.sector && (
            <span className="text-sm text-gray-600 dark:text-gray-400">{live.sector}</span>
          )}
        </div>
        <div className="mt-2 text-3xl">
          <PriceCell value={live.ltp} pct={live.pct_change} />
        </div>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Open" value={live.open} />
        <Stat label="High" value={live.high} />
        <Stat label="Low" value={live.low} />
        <Stat label="Prev close" value={live.prev_close} />
      </section>

      {f && (
        <>
          <section>
            <h2 className="text-lg font-semibold mb-2">52-week range</h2>
            {f.week_52_low && f.week_52_high && (
              <div className="space-y-2">
                <div className="relative h-3 bg-gray-200 dark:bg-gray-800 rounded-full">
                  {pricePos != null && (
                    <div
                      className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-600 rounded-full ring-2 ring-white dark:ring-gray-900"
                      style={{ left: `calc(${Math.max(0, Math.min(100, pricePos))}% - 6px)` }}
                    />
                  )}
                </div>
                <div className="flex justify-between text-xs text-gray-500 tabular-nums">
                  <span>{f.week_52_low.toFixed(2)} (low)</span>
                  <span>{f.week_52_high.toFixed(2)} (high)</span>
                </div>
              </div>
            )}
          </section>

          <section>
            <h2 className="text-lg font-semibold mb-2">Fundamentals</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <Stat label="P/E ratio" value={f.pe_ratio} />
              <Stat
                label={`EPS${f.eps_period ? ` (${f.eps_period})` : ""}`}
                value={f.eps}
              />
              <Stat label="Book value" value={f.book_value} />
              <Stat label="120-day avg" value={f.avg_120_day} />
              <Stat label="180-day avg" value={f.avg_180_day} />
              <Stat
                label="1Y yield"
                value={f.yield_pct == null ? null : `${f.yield_pct.toFixed(2)}%`}
              />
              <Stat
                label={`Dividend${f.dividend_period ? ` (${f.dividend_period})` : ""}`}
                value={f.dividend_pct == null ? null : `${f.dividend_pct.toFixed(2)}%`}
              />
              <Stat
                label="Market cap"
                value={f.market_cap == null ? null : `Rs ${(f.market_cap / 1e9).toFixed(2)} B`}
              />
              <Stat
                label="Listed shares"
                value={f.listed_shares == null ? null : (f.listed_shares / 1e6).toFixed(2) + " M"}
              />
            </div>
          </section>
        </>
      )}

      {!f && (
        <p className="text-sm text-amber-700 dark:text-amber-400">
          Fundamentals not yet loaded. They are fetched in the background when a stock is added to
          a portfolio, then refreshed daily after market close.
        </p>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number | string | null | undefined }) {
  let displayed: string
  if (value == null) displayed = "—"
  else if (typeof value === "number") displayed = fmtMoney(value)
  else displayed = value
  return (
    <div className="rounded border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-base font-semibold mt-1 tabular-nums">{displayed}</div>
    </div>
  )
}
