import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client"
import type { PolicyRateRow } from "../api/types"
import { fmtMoney } from "../components/PriceCell"

export function Policy() {
  const ratesQ = useQuery({ queryKey: ["policy-rates"], queryFn: api.getPolicyRates })
  const macroQ = useQuery({
    queryKey: ["policy-macro"],
    queryFn: api.getMacro,
    refetchInterval: 60_000 * 30,
  })
  const newsQ = useQuery({
    queryKey: ["news", "monetary+fiscal"],
    queryFn: async () => {
      const [m, f] = await Promise.all([
        api.getNews("monetary", 20),
        api.getNews("fiscal", 20),
      ])
      const seen = new Set<string>()
      return [...m, ...f].filter((a) => {
        if (seen.has(a.slug)) return false
        seen.add(a.slug)
        return true
      })
    },
    refetchInterval: 60_000 * 5,
  })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Policy watch</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Monetary policy (set by NRB) controls how much money flows through banks — it tilts
          deposit and lending rates, which moves bank and finance stocks. Fiscal policy (set by
          the Ministry of Finance via the annual budget) controls tax rates including capital
          gains tax and dividend tax — that's what shows up directly in your "net P&amp;L if sold"
          number.
        </p>
        <p className="text-xs text-amber-700 dark:text-amber-400 mt-2">
          The rate numbers below are <strong>manually maintained</strong> — they only change 1–2
          times per year and auto-scraping the PDFs is error-prone. Check the official sources
          at the bottom if you need to verify.
        </p>
      </header>

      {macroQ.data?.available && macroQ.data.banking && (
        <section>
          <h2 className="text-lg font-semibold mb-2">
            Banking system snapshot
            <span className="text-xs text-gray-500 ml-2">
              as of {macroQ.data.as_of} · live from NRB
            </span>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat
              label="Total deposits"
              value={`NPR ${fmtMoney(macroQ.data.banking.total_deposits_npr_bn, 0)} B`}
            />
            <Stat
              label="Total lending"
              value={`NPR ${fmtMoney(macroQ.data.banking.total_lending_npr_bn, 0)} B`}
            />
            <Stat
              label="CD ratio"
              value={
                macroQ.data.banking.cd_ratio_pct == null
                  ? "—"
                  : `${macroQ.data.banking.cd_ratio_pct.toFixed(2)}%`
              }
              sub="banks: how much of deposits is loaned out"
            />
            <Stat
              label="Commercial bank loans"
              value={`NPR ${fmtMoney(macroQ.data.banking.commercial_banks_lending_npr_bn, 0)} B`}
            />
          </div>
          {macroQ.data.forex && macroQ.data.forex.length > 0 && (
            <div className="mt-3 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                Forex (NRB indicative)
              </div>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-sm">
                {macroQ.data.forex.map((f) => (
                  <div key={f.currency} className="flex items-baseline gap-2">
                    <span className="font-mono text-xs text-gray-500">{f.currency}</span>
                    <span className="tabular-nums">{f.buy.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {ratesQ.data && (
        <>
          <section>
            <h2 className="text-lg font-semibold mb-2">Monetary policy rates</h2>
            <RateTable rows={ratesQ.data.monetary_rates} />
          </section>
          <section>
            <h2 className="text-lg font-semibold mb-2">Fiscal policy — what taxes you</h2>
            <RateTable rows={ratesQ.data.fiscal_highlights} />
          </section>
        </>
      )}

      {newsQ.data && newsQ.data.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Recent policy news</h2>
          <ul className="space-y-1.5">
            {newsQ.data.slice(0, 10).map((a) => (
              <li key={a.slug} className="text-sm">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 dark:text-blue-300 hover:underline"
                >
                  {a.title}
                </a>
                <span className="text-xs text-gray-500 ml-2">
                  {a.policy_tags.map((t) => `#${t}`).join(" ")}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {ratesQ.data && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Official sources</h2>
          <ul className="space-y-2">
            {ratesQ.data.links.map((l) => (
              <li
                key={l.url}
                className="rounded border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3"
              >
                <a
                  href={l.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-blue-700 dark:text-blue-300 hover:underline"
                >
                  {l.title}
                </a>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{l.blurb}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

function RateTable({ rows }: { rows: PolicyRateRow[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr className="text-left">
            <th className="px-3 py-2">Rate</th>
            <th className="px-3 py-2 text-right">Value</th>
            <th className="px-3 py-2">Effective</th>
            <th className="px-3 py-2">What it means</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name} className="border-t border-gray-100 dark:border-gray-800 align-top">
              <td className="px-3 py-2 font-medium">{r.name}</td>
              <td className="px-3 py-2 text-right tabular-nums font-semibold">
                {r.value}
                {r.unit}
              </td>
              <td className="px-3 py-2 text-xs text-gray-500">{r.effective_date}</td>
              <td className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400">{r.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
}: {
  label: string
  value: string
  sub?: string
}) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-base font-semibold mt-1 tabular-nums">{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-1">{sub}</div>}
    </div>
  )
}
