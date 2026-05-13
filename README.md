# NEPSE Portfolio

A small web app for tracking your NEPSE portfolio and getting fundamentals-based "should I think about selling?" signals — without empty promises about predicting prices.

## What it does

- Pulls live trading data for **all NEPSE stocks** from Sharesansar (every 30s during market hours, Sun–Thu 11:00–15:00 NPT).
- Pulls fundamentals (P/E, EPS, book value, 52-week H/L, moving averages, dividends) from Mero Lagani — once a day, only for stocks anyone is holding.
- Lets you log in with **just a username** (no password) and save your holdings.
- Runs your holdings through a rule-based signal engine and explains each signal in plain English:
  - Profit target reached
  - Near 52-week high / low
  - Below moving averages
  - Strong dividend → likely hold
  - Valuation stretched vs sector (when sector data is sufficient)
  - Loss + downtrend
- Provides a **Learn** tab with English and Nepali explanations of the basics.

## What it does NOT do

- It does **not** predict the exact date/time of the next high or low. Nothing can.
- The username login has **no privacy** — anyone who knows your username can read or change that portfolio. Pick something only you would think of.
- It does **not** auto-generate monetary/fiscal policy "analysis." Nepali macro data is too sparse for confident automated takes; we surface the raw rates + plain-English explainers and link out to NRB/MoF documents instead.

## New: News and Policy

- **News tab** scrapes Sharesansar's news listing every 30 minutes. Articles are auto-tagged:
  - `#monetary` — NRB, policy rate, CRR/SLR, liquidity
  - `#fiscal` — budget, Finance Ministry, tax changes, SEBON
  - `#macro` — GDP, inflation, remittance, BoP
  - `#corporate_action` — IPO, bonus, rights, dividend, AGM, merger
  - Any of your held NEPSE symbols mentioned in the headline.
  - Filter "Affecting my portfolio" → only shows articles that mention symbols you hold.
- **Policy tab** combines:
  - Live banking-system snapshot from NRB (total deposits, total lending, CD ratio, forex rates).
  - Current monetary policy rates (Policy Rate / Bank Rate / CRR / SLR) with plain-English explanations of what each lever does.
  - Current fiscal policy hits to your wallet (CGT short/long term, dividend tax, SEBON levy).
  - Recent policy-tagged news.
  - Direct links to NRB, Ministry of Finance, SEBON, and NEPSE official sources.

## Repo layout

```
nepse-portfolio/
├── backend/
│   ├── app/                  # FastAPI app
│   │   ├── main.py           # FastAPI + lifespan that starts the scheduler
│   │   ├── scheduler.py      # APScheduler jobs (30s live + daily fundamentals)
│   │   ├── signals.py        # rule-based signal engine
│   │   ├── rate_limit.py     # tiny in-memory IP rate limiter for writes
│   │   ├── scraper/          # Sharesansar + Mero Lagani scrapers
│   │   ├── db/               # SQLModel schema + engine + repo
│   │   └── routes/           # /stocks, /users, /users/{u}/holdings, /users/{u}/analysis
│   ├── data/                 # SQLite file lives here (gitignored)
│   └── requirements.txt
└── frontend/                 # Vite + React + TypeScript + Tailwind v4
    └── src/
        ├── api/              # typed client + types
        ├── components/       # Layout, UsernameModal, SignalBadge, PriceCell
        ├── hooks/            # useUsername (localStorage)
        ├── pages/            # Dashboard, Portfolio, Stocks, StockDetail, Learn
        └── content/learn/    # markdown topics, en + ne side by side
```

## Running locally

### Backend

Requires Python 3.11+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Visit `http://localhost:8765/docs` for the auto-generated OpenAPI explorer.

### Frontend

Requires Node 20+.

```powershell
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. On first load it asks for a username.

## API endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | liveness check |
| GET | `/stocks?sector=X&limit=N` | list latest live prices |
| GET | `/stocks/{symbol}` | live + fundamentals for one symbol |
| POST | `/users` | claim a username (idempotent) |
| GET | `/users/{u}/holdings` | list a user's holdings |
| POST | `/users/{u}/holdings` | add a holding (also warm-fetches fundamentals in the background) |
| DELETE | `/users/{u}/holdings/{id}` | remove a holding |
| GET | `/users/{u}/analysis` | run signals engine + P&L for the user's portfolio |

Write endpoints are rate-limited to 30 requests / minute per client IP.

## Data sources & politeness

- `https://www.sharesansar.com/live-trading` — HTML scrape, 30s cadence during market hours.
- `https://merolagani.com/CompanyDetail.aspx?symbol=...` — HTML scrape, daily for held stocks, with 1.5s delay between requests.

Both sites are scraped read-only with a normal browser User-Agent. Be polite — if you fork this, don't crank the refresh rate.

## License

Personal use. No warranty. The signals are heuristics, not financial advice.
