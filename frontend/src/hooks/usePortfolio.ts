import { useEffect, useState } from "react"

const STORAGE_KEY = "nepse_portfolio_v2"

export interface LocalHolding {
  client_id: string
  symbol: string
  qty: number
  buy_price: number
  buy_date: string // ISO date 'YYYY-MM-DD' or full ISO timestamp
  target_pct: number | null
}

interface PortfolioState {
  holdings: LocalHolding[]
  last_modified: string
}

function load(): PortfolioState {
  if (typeof window === "undefined") return empty()
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return empty()
    const parsed = JSON.parse(raw) as PortfolioState
    if (!Array.isArray(parsed.holdings)) return empty()
    return parsed
  } catch {
    return empty()
  }
}

function empty(): PortfolioState {
  return { holdings: [], last_modified: new Date().toISOString() }
}

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID()
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function usePortfolio() {
  const [state, setState] = useState<PortfolioState>(load)

  // Cross-tab sync.
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setState(load())
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  function save(next: PortfolioState) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setState(next)
  }

  function addHolding(input: Omit<LocalHolding, "client_id">) {
    const h: LocalHolding = { client_id: newId(), ...input }
    save({ holdings: [...state.holdings, h], last_modified: new Date().toISOString() })
  }

  function removeHolding(client_id: string) {
    save({
      holdings: state.holdings.filter((h) => h.client_id !== client_id),
      last_modified: new Date().toISOString(),
    })
  }

  function clearAll() {
    save({ holdings: [], last_modified: new Date().toISOString() })
  }

  function exportJson(): string {
    return JSON.stringify(state, null, 2)
  }

  function importJson(raw: string): { ok: boolean; error?: string } {
    try {
      const parsed = JSON.parse(raw)
      if (!parsed || !Array.isArray(parsed.holdings)) return { ok: false, error: "no holdings array" }
      save({
        holdings: parsed.holdings.map((h: LocalHolding) => ({
          client_id: h.client_id || newId(),
          symbol: String(h.symbol).toUpperCase(),
          qty: Number(h.qty),
          buy_price: Number(h.buy_price),
          buy_date: String(h.buy_date),
          target_pct: h.target_pct == null ? null : Number(h.target_pct),
        })),
        last_modified: new Date().toISOString(),
      })
      return { ok: true }
    } catch (e) {
      return { ok: false, error: e instanceof Error ? e.message : "invalid JSON" }
    }
  }

  return {
    holdings: state.holdings,
    addHolding,
    removeHolding,
    clearAll,
    exportJson,
    importJson,
  }
}
