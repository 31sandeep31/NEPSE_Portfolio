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

export interface FeeBreakdown {
  broker_commission: number
  sebon_levy: number
  dp_charge: number
  capital_gains_tax: number
  cgt_rate: number
  total: number
}

export interface HoldingAnalysis {
  holding_id: number
  symbol: string
  qty: number
  buy_price: number
  cost_basis: number
  cost_basis_with_fees: number
  current_price: number | null
  current_value: number | null
  unrealized_pl: number | null
  unrealized_pl_pct: number | null
  net_proceeds_if_sold: number | null
  net_pl_if_sold: number | null
  net_pl_pct_if_sold: number | null
  sell_fees: FeeBreakdown | null
  target_pct: number | null
  signals: Signal[]
}

export interface PortfolioAnalysis {
  username: string
  as_of: string
  market_open: boolean | null
  last_price_update: string | null
  total_cost_basis: number
  total_cost_basis_with_fees: number
  total_current_value: number | null
  total_unrealized_pl: number | null
  total_unrealized_pl_pct: number | null
  total_net_proceeds_if_sold: number | null
  total_net_pl_if_sold: number | null
  total_net_pl_pct_if_sold: number | null
  holdings: HoldingAnalysis[]
  warnings: string[]
}

export interface PriceBar {
  date: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  volume: number | null
}

export interface MoverRow {
  symbol: string
  ltp: number | null
  pct_change: number | null
  qty: number | null
  sector: string | null
}

export interface SectorSummary {
  sector: string
  count: number
  avg_pct_change: number
  up: number
  down: number
}

export interface MoversResponse {
  gainers: MoverRow[]
  losers: MoverRow[]
  by_volume: MoverRow[]
  sector_summary: SectorSummary[]
}
