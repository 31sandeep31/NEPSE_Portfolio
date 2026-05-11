import { useState } from "react"
import ReactMarkdown from "react-markdown"
import basicsEn from "../content/learn/stock-market-basics.en.md?raw"
import basicsNe from "../content/learn/stock-market-basics.ne.md?raw"
import fundamentalsEn from "../content/learn/pe-eps-book-value.en.md?raw"
import fundamentalsNe from "../content/learn/pe-eps-book-value.ne.md?raw"
import whenSellEn from "../content/learn/when-to-sell.en.md?raw"
import whenSellNe from "../content/learn/when-to-sell.ne.md?raw"

type Lang = "en" | "ne"

interface Topic {
  slug: string
  title: { en: string; ne: string }
  body: { en: string; ne: string }
}

const TOPICS: Topic[] = [
  {
    slug: "stock-market-basics",
    title: { en: "Stock market basics", ne: "शेयर बजार के हो?" },
    body: { en: basicsEn, ne: basicsNe },
  },
  {
    slug: "pe-eps-book-value",
    title: { en: "P/E, EPS, Book value", ne: "P/E, EPS, Book value" },
    body: { en: fundamentalsEn, ne: fundamentalsNe },
  },
  {
    slug: "when-to-sell",
    title: { en: "When to sell — simple rules", ne: "कहिले बेच्ने" },
    body: { en: whenSellEn, ne: whenSellNe },
  },
]

export function Learn() {
  const [lang, setLang] = useState<Lang>("en")
  const [active, setActive] = useState(TOPICS[0].slug)
  const topic = TOPICS.find((t) => t.slug === active)!

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">Learn</h1>
        <div className="flex gap-1 text-sm">
          <button
            onClick={() => setLang("en")}
            className={`px-3 py-1 rounded ${
              lang === "en" ? "bg-blue-600 text-white" : "bg-gray-200 dark:bg-gray-800"
            }`}
          >
            English
          </button>
          <button
            onClick={() => setLang("ne")}
            className={`px-3 py-1 rounded ${
              lang === "ne" ? "bg-blue-600 text-white" : "bg-gray-200 dark:bg-gray-800"
            }`}
          >
            नेपाली
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-6">
        <nav className="rounded-lg border border-gray-200 dark:border-gray-800 p-2 h-fit">
          <ul className="space-y-1">
            {TOPICS.map((t) => (
              <li key={t.slug}>
                <button
                  onClick={() => setActive(t.slug)}
                  className={`w-full text-left px-3 py-2 rounded text-sm ${
                    active === t.slug
                      ? "bg-blue-600 text-white"
                      : "hover:bg-gray-100 dark:hover:bg-gray-800"
                  }`}
                >
                  {t.title[lang]}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <article className="prose prose-sm dark:prose-invert max-w-none rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6">
          <MarkdownView content={topic.body[lang]} />
        </article>
      </div>
    </div>
  )
}

function MarkdownView({ content }: { content: string }) {
  return (
    <div className="space-y-3 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:mt-2 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:mt-4 [&_h3]:font-semibold [&_h3]:mt-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:my-1 [&_p]:leading-relaxed [&_code]:px-1 [&_code]:py-0.5 [&_code]:bg-gray-100 [&_code]:dark:bg-gray-800 [&_code]:rounded">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}
