import { NavLink, Outlet } from "react-router-dom"
import { useUsername } from "../hooks/useUsername"

export function Layout() {
  const { username, setUsername } = useUsername()

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
            NEPSE <span className="text-blue-600">Portfolio</span>
          </NavLink>
          <nav className="flex items-center gap-1">
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
          <div className="text-sm">
            {username ? (
              <button
                onClick={() => {
                  if (confirm(`Sign out of "${username}"?`)) setUsername(null)
                }}
                className="px-3 py-1 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
                title="Click to sign out"
              >
                {username}
              </button>
            ) : (
              <span className="text-gray-500">no user</span>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
      <footer className="text-xs text-gray-500 text-center py-4 border-t border-gray-200 dark:border-gray-800">
        Data: Sharesansar (live), Mero Lagani (fundamentals). Signals are heuristics, not predictions.
      </footer>
    </div>
  )
}
