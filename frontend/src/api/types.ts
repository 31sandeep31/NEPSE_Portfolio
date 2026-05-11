export interface Stock {
  symbol: string
  sector: string | null
  ltp: number | null
  point_change: number | null
  pct_change: number | null
  open: number | null
  high: number | null
  low: number | null
  qty: number | null
  prev_close: number | null
  updated_at: string | null
}

export interface Fundamentals {
  sector: string | null
  eps: number | null
  eps_period: string | null
  pe_ratio: number | null
  book_value: number | null
  market_cap: number | null
  week_52_high: number | null
  week_52_low: number | null
  avg_120_day: number | null
  avg_180_day: number | null
  yield_pct: number | null
  dividend_pct: number | null
  dividend_period: string | null
  listed_shares: number | null
  paidup_value: number | null
  fetched_at: string | null
}

export interface StockDetail {
  live: Stock
  fundamentals: Fundamentals | null
}

export interface Holding {
  id: number
  username: string
  symbol: string
  qty: number
  buy_price: number
  buy_date: string
  target_pct: number | null
  created_at: string
}

export interface HoldingInput {
  symbol: string
  qty: number
  buy_price: number
  buy_date: string
  target_pct?: number | null
}

export type SignalLevel =
  | "info"
  | "hold"
  | "watch"
  | "consider_sell"
  | "target_hit"
  | "loss_alert"

export interface Signal {
  rule: string
  level: SignalLevel
  title: string
  explanation: string
  data: Record<string, unknown>
}

export interface HoldingAnalysis {
  holding_id: number
  symbol: string
  qty: number
  buy_price: number
  cost_basis: number
  current_price: number | null
  current_value: number | null
  unrealized_pl: number | null
  unrealized_pl_pct: number | null
  target_pct: number | null
  signals: Signal[]
}

export interface PortfolioAnalysis {
  username: string
  as_of: string
  market_open: boolean | null
  last_price_update: string | null
  total_cost_basis: number
  total_current_value: number | null
  total_unrealized_pl: number | null
  total_unrealized_pl_pct: number | null
  holdings: HoldingAnalysis[]
  warnings: string[]
}
