import type { Signal, SignalLevel } from "../api/types"

const LEVEL_STYLES: Record<SignalLevel, string> = {
  info: "bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
  hold: "bg-blue-50 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800",
  watch: "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
  consider_sell: "bg-orange-50 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800",
  target_hit: "bg-green-50 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800",
  loss_alert: "bg-red-50 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
}

export function SignalBadge({ signal }: { signal: Signal }) {
  return (
    <div className={`border rounded-md p-3 text-sm ${LEVEL_STYLES[signal.level]}`}>
      <div className="font-semibold">{signal.title}</div>
      <p className="mt-1 opacity-90">{signal.explanation}</p>
    </div>
  )
}
