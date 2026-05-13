import { BrowserRouter, Route, Routes } from "react-router-dom"
import { Layout } from "./components/Layout"
import { Dashboard } from "./pages/Dashboard"
import { Learn } from "./pages/Learn"
import { News } from "./pages/News"
import { Policy } from "./pages/Policy"
import { Portfolio } from "./pages/Portfolio"
import { Stocks } from "./pages/Stocks"
import { StockDetail } from "./pages/StockDetail"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="stocks" element={<Stocks />} />
          <Route path="stocks/:symbol" element={<StockDetail />} />
          <Route path="news" element={<News />} />
          <Route path="policy" element={<Policy />} />
          <Route path="learn" element={<Learn />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
