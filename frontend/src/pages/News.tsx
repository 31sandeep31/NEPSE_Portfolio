import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { api } from "../api/client"
import type { NewsArticle } from "../api/types"
import { usePortfolio } from "../hooks/usePortfolio"

type Filter = "all" | "mine" | "monetary" | "fiscal" | "macro" | "corporate_action"

const FILTERS: { key: Filter; label: string; help: string }[] = [
  { key: "all", label: "All", help: "Everything scraped from Sharesansar" },
  { key: "mine", label: "Affecting my portfolio", help: "Articles that mention any of your held symbols" },
  { key: "monetary", label: "Monetary", help: "NRB, policy rate, CRR/SLR, interest rates, liquidity" },
  { key: "fiscal", label: "Fiscal", help: "Budget, Finance Ministry, tax changes, SEBON" },
  { key: "macro", label: "Macro", help: "GDP, inflation, remittance, BoP" },
  { key: "corporate_action", label: "Corporate actions", help: "Bonus, rights, IPO, dividend, AGM" },
]

export function News() {
  const { holdings } = usePortfolio()
  const [filter, setFilter] = useState<Filter>("all")
  const heldSymbols = holdings.map((h) => h.symbol)

  const allQ = useQuery({
    queryKey: ["news", filter === "mine" ? "all" : filter],
    queryFn: () =>
      api.getNews(filter === "mine" ? "all" : (filter as Exclude<Filter, "mine">), 100),
    refetchInterval: 60_000 * 5,
    enabled: filter !== "mine",
  })

  const mineQ = useQuery({
    queryKey: ["news", "relevant", heldSymbols.join(",")],
    queryFn: () => api.postRelevantNews(heldSymbols, 100),
    enabled: filter === "mine" && heldSymbols.length > 0,
    refetchInterval: 60_000 * 5,
  })

  const data = filter === "mine" ? mineQ.data : allQ.data
  const isLoading = filter === "mine" ? mineQ.isLoading : allQ.isLoading
  const error = filter === "mine" ? mineQ.error : allQ.error

  return (
    <div className="space-y-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">News</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Pulled from Sharesansar every 30 min. Articles are tagged by topic and by any NEPSE
          symbol they mention.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const disabled = f.key === "mine" && heldSymbols.length === 0
          return (
            <button
              key={f.key}
              disabled={disabled}
              onClick={() => setFilter(f.key)}
              title={disabled ? "Add a holding first" : f.help}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                filter === f.key
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
              } ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}
            >
              {f.label}
            </button>
          )
        })}
      </div>

      {isLoading && <p className="text-gray-500 text-sm">Loading...</p>}
      {error && (
        <p className="text-red-600 text-sm">
          {error instanceof Error ? error.message : "Failed"}
        </p>
      )}

      {data && data.length === 0 && (
        <p className="text-gray-500 text-sm py-8 text-center">
          {filter === "mine"
            ? "None of your held stocks have been mentioned in recent news yet."
            : "No articles matching this filter yet — refresh in a few minutes."}
        </p>
      )}

      <ul className="space-y-2">
        {data?.map((a) => (
          <NewsRow key={a.slug} article={a} />
        ))}
      </ul>
    </div>
  )
}

function NewsRow({ article }: { article: NewsArticle }) {
  const date =
    article.published_date ??
    (article.fetched_at ? new Date(article.fetched_at).toISOString().slice(0, 10) : null)
  return (
    <li className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium text-sm hover:underline text-blue-700 dark:text-blue-300"
      >
        {article.title}
      </a>
      <div className="mt-1 flex flex-wrap gap-1.5 text-[11px]">
        {date && <span className="text-gray-500">{date}</span>}
        {article.policy_tags.map((t) => (
          <span key={t} className={tagClass("policy")}>
            #{t}
          </span>
        ))}
        {article.sector_tags.map((t) => (
          <span key={t} className={tagClass("sector")}>
            {t}
          </span>
        ))}
        {article.symbols_mentioned.map((t) => (
          <span key={t} className={tagClass("symbol")}>
            {t}
          </span>
        ))}
      </div>
    </li>
  )
}

function tagClass(kind: "policy" | "sector" | "symbol"): string {
  if (kind === "policy")
    return "px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
  if (kind === "symbol")
    return "px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 font-mono"
  return "px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
}
