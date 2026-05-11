export function PriceCell({ value, pct }: { value: number | null; pct?: number | null }) {
  if (value == null) return <span className="text-gray-400">—</span>
  const color =
    pct == null ? "" : pct > 0 ? "text-green-600 dark:text-green-400" : pct < 0 ? "text-red-600 dark:text-red-400" : ""
  return (
    <span className={`tabular-nums ${color}`}>
      {value.toFixed(2)}
      {pct != null && (
        <span className="ml-1 text-xs opacity-80">
          {pct > 0 ? "+" : ""}
          {pct.toFixed(2)}%
        </span>
      )}
    </span>
  )
}

export function fmtMoney(v: number | null | undefined, digits = 2): string {
  if (v == null) return "—"
  return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}
