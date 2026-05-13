import { useState } from "react"
import { Link } from "react-router-dom"
import { fmtMoney } from "../components/PriceCell"
import { usePortfolio } from "../hooks/usePortfolio"

export function Portfolio() {
  const { holdings, addHolding, removeHolding, clearAll, exportJson, importJson } = usePortfolio()
  const [showImport, setShowImport] = useState(false)
  const [importText, setImportText] = useState("")
  const [importErr, setImportErr] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <header className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Your portfolio</h1>
          <p className="text-xs text-gray-500 mt-1">
            Stored only in this browser. No login. Use Export/Import to move between devices.
          </p>
        </div>
        <div className="flex gap-2 text-xs">
          <button
            onClick={() => {
              navigator.clipboard.writeText(exportJson())
              alert("Portfolio JSON copied to clipboard.")
            }}
            disabled={holdings.length === 0}
            className="px-3 py-1.5 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40"
          >
            Export
          </button>
          <button
            onClick={() => setShowImport((v) => !v)}
            className="px-3 py-1.5 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Import
          </button>
          <button
            onClick={() => {
              if (holdings.length > 0 && confirm("Delete all holdings? This cannot be undone."))
                clearAll()
            }}
            disabled={holdings.length === 0}
            className="px-3 py-1.5 rounded border border-red-300 text-red-700 dark:border-red-800 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
          >
            Clear
          </button>
        </div>
      </header>

      {showImport && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3 space-y-2">
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder='Paste exported JSON here, e.g. {"holdings":[...]}'
            className="w-full h-24 px-2 py-1.5 text-xs font-mono border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded"
          />
          <div className="flex gap-2 items-center">
            <button
              onClick={() => {
                const r = importJson(importText)
                if (r.ok) {
                  setImportText("")
                  setImportErr(null)
                  setShowImport(false)
                } else {
                  setImportErr(r.error ?? "import failed")
                }
              }}
              className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs"
            >
              Replace portfolio with this
            </button>
            {importErr && <span className="text-xs text-red-600">{importErr}</span>}
          </div>
        </div>
      )}

      <AddHoldingForm onAdd={addHolding} />

      <section>
        <h2 className="text-lg font-semibold mb-2">Holdings</h2>
        {holdings.length === 0 ? (
          <p className="text-gray-500 text-sm">No holdings yet. Add one above.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr className="text-left">
                  <th className="px-3 py-2">Symbol</th>
                  <th className="px-3 py-2 text-right">Qty</th>
                  <th className="px-3 py-2 text-right">Buy price</th>
                  <th className="px-3 py-2">Buy date</th>
                  <th className="px-3 py-2 text-right">Target %</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.client_id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-3 py-2 font-mono">
                      <Link to={`/stocks/${h.symbol}`} className="text-blue-600 hover:underline">
                        {h.symbol}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{h.qty}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtMoney(h.buy_price)}</td>
                    <td className="px-3 py-2">{h.buy_date.slice(0, 10)}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {h.target_pct == null ? "—" : `${h.target_pct.toFixed(1)}%`}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => {
                          if (confirm(`Remove ${h.qty} × ${h.symbol}?`)) removeHolding(h.client_id)
                        }}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

interface AddInput {
  symbol: string
  qty: number
  buy_price: number
  buy_date: string
  target_pct: number | null
}

function AddHoldingForm({ onAdd }: { onAdd: (h: AddInput) => void }) {
  const [form, setForm] = useState<AddInput>({
    symbol: "",
    qty: 0,
    buy_price: 0,
    buy_date: new Date().toISOString().slice(0, 10),
    target_pct: null,
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (!form.symbol.trim() || form.qty <= 0 || form.buy_price <= 0) return
        onAdd({ ...form, symbol: form.symbol.toUpperCase().trim() })
        setForm((f) => ({ ...f, symbol: "", qty: 0, buy_price: 0 }))
      }}
      className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4"
    >
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Field label="Symbol">
          <input
            required
            value={form.symbol}
            onChange={(e) => setForm({ ...form, symbol: e.target.value })}
            placeholder="NABIL"
            className={inputCls}
          />
        </Field>
        <Field label="Quantity">
          <input
            required
            type="number"
            min={0.0001}
            step="any"
            value={form.qty || ""}
            onChange={(e) => setForm({ ...form, qty: Number(e.target.value) })}
            className={inputCls}
          />
        </Field>
        <Field label="Buy price">
          <input
            required
            type="number"
            min={0.01}
            step="any"
            value={form.buy_price || ""}
            onChange={(e) => setForm({ ...form, buy_price: Number(e.target.value) })}
            className={inputCls}
          />
        </Field>
        <Field label="Buy date">
          <input
            required
            type="date"
            value={form.buy_date.slice(0, 10)}
            onChange={(e) => setForm({ ...form, buy_date: e.target.value })}
            className={inputCls}
          />
        </Field>
        <Field label="Target % (optional)">
          <input
            type="number"
            step="any"
            value={form.target_pct ?? ""}
            onChange={(e) =>
              setForm({ ...form, target_pct: e.target.value === "" ? null : Number(e.target.value) })
            }
            placeholder="e.g. 15"
            className={inputCls}
          />
        </Field>
      </div>
      <div className="mt-3">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Add holding
        </button>
      </div>
    </form>
  )
}

const inputCls =
  "w-full px-2 py-1.5 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}
