import type {
  Holding,
  HoldingInput,
  PortfolioAnalysis,
  Stock,
  StockDetail,
} from "./types"

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8765"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!r.ok) {
    const body = await r.text().catch(() => "")
    throw new Error(`${r.status} ${r.statusText}: ${body || path}`)
  }
  return r.json() as Promise<T>
}

export const api = {
  listStocks: (sector?: string) =>
    request<Stock[]>(`/stocks${sector ? `?sector=${encodeURIComponent(sector)}` : ""}`),

  getStock: (symbol: string) => request<StockDetail>(`/stocks/${symbol}`),

  claimUsername: (username: string) =>
    request<{ username: string; created_at: string }>("/users", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),

  listHoldings: (username: string) =>
    request<Holding[]>(`/users/${username}/holdings`),

  addHolding: (username: string, body: HoldingInput) =>
    request<Holding>(`/users/${username}/holdings`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  deleteHolding: (username: string, id: number) =>
    request<{ deleted: number }>(`/users/${username}/holdings/${id}`, {
      method: "DELETE",
    }),

  getAnalysis: (username: string) =>
    request<PortfolioAnalysis>(`/users/${username}/analysis`),
}
