import type {
  Holding,
  HoldingInput,
  MacroResponse,
  MoversResponse,
  NewsArticle,
  PolicyRatesResponse,
  PortfolioAnalysis,
  PriceBar,
  Stock,
  StockDetail,
} from "./types"

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8765"

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

  getStockHistory: (symbol: string, days = 90) =>
    request<PriceBar[]>(`/stocks/${symbol}/history?days=${days}`),

  getMovers: (limit = 5) => request<MoversResponse>(`/movers?limit=${limit}`),

  getNews: (filter: "all" | "monetary" | "fiscal" | "macro" | "corporate_action" = "all", limit = 100) =>
    request<NewsArticle[]>(`/news?filter=${filter}&limit=${limit}`),

  getNewsForUser: (username: string, limit = 100) =>
    request<NewsArticle[]>(`/news/for-user/${username}?limit=${limit}`),

  getPolicyRates: () => request<PolicyRatesResponse>("/policy/rates"),

  getMacro: () => request<MacroResponse>("/policy/macro"),

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
