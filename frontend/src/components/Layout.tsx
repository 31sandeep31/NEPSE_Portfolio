import { NavLink, Outlet } from "react-router-dom"

export function Layout() {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? "bg-blue-600 text-white"
        : "text-gray-700 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800"
    }`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <NavLink to="/" className="text-lg font-semibold tracking-tight">
            My <span className="text-blue-600">Nepse</span>
          </NavLink>
          <nav className="flex items-center gap-1 flex-wrap">
            <NavLink to="/" end className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/portfolio" className={navClass}>
              Portfolio
            </NavLink>
            <NavLink to="/stocks" className={navClass}>
              Stocks
            </NavLink>
            <NavLink to="/news" className={navClass}>
              News
            </NavLink>
            <NavLink to="/policy" className={navClass}>
              Policy
            </NavLink>
            <NavLink to="/learn" className={navClass}>
              Learn
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
      <footer className="text-xs text-gray-500 text-center py-4 border-t border-gray-200 dark:border-gray-800">
        Data: Sharesansar (live + news), Mero Lagani (fundamentals), NRB (macro). Signals are heuristics, not predictions. Portfolio is stored only in your browser.
      </footer>
    </div>
  )
}
