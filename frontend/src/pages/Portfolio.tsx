import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../api/client"
import type { HoldingInput } from "../api/types"
import { fmtMoney } from "../components/PriceCell"
import { useUsername } from "../hooks/useUsername"

export function Portfolio() {
  const { username } = useUsername()
  const qc = useQueryClient()

  const holdings = useQuery({
    queryKey: ["holdings", username],
    queryFn: () => api.listHoldings(username!),
    enabled: !!username,
  })

  const removeMut = useMutation({
    mutationFn: (id: number) => api.deleteHolding(username!, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["holdings", username] })
      qc.invalidateQueries({ queryKey: ["analysis", username] })
    },
  })

  if (!username) return null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Your portfolio</h1>

      <AddHoldingForm />

      <section>
        <h2 className="text-lg font-semibold mb-2">Holdings</h2>
        {holdings.isLoading ? (
          <p className="text-gray-500">Loading...</p>
        ) : !holdings.data?.length ? (
          <p className="text-gray-500">No holdings yet. Add one above.</p>
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
                {holdings.data.map((h) => (
                  <tr key={h.id} className="border-t border-gray-100 dark:border-gray-800">
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
                          if (confirm(`Remove ${h.qty} × ${h.symbol}?`)) removeMut.mutate(h.id)
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

function AddHoldingForm() {
  const { username } = useUsername()
  const qc = useQueryClient()
  const [form, setForm] = useState<HoldingInput>({
    symbol: "",
    qty: 0,
    buy_price: 0,
    buy_date: new Date().toISOString().slice(0, 10),
    target_pct: null,
  })
  const [error, setError] = useState<string | null>(null)

  const addMut = useMutation({
    mutationFn: (body: HoldingInput) =>
      api.addHolding(username!, {
        ...body,
        symbol: body.symbol.toUpperCase().trim(),
        buy_date: new Date(body.buy_date).toISOString(),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["holdings", username] })
      qc.invalidateQueries({ queryKey: ["analysis", username] })
      setForm((f) => ({ ...f, symbol: "", qty: 0, buy_price: 0 }))
      setError(null)
    },
    onError: (e) => setError(e instanceof Error ? e.message : "Failed"),
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        addMut.mutate(form)
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
      <div className="mt-3 flex items-center gap-3">
        <button
          type="submit"
          disabled={addMut.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {addMut.isPending ? "Adding..." : "Add holding"}
        </button>
        {error && <span className="text-sm text-red-600">{error}</span>}
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
