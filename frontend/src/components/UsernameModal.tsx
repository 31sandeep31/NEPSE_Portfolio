import { useState } from "react"
import { api } from "../api/client"
import { useUsername } from "../hooks/useUsername"

export function UsernameModal() {
  const { setUsername } = useUsername()
  const [value, setValue] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const r = await api.claimUsername(value.trim())
      setUsername(r.username)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <form
        onSubmit={onSubmit}
        className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full p-6 space-y-4"
      >
        <div>
          <h2 className="text-xl font-semibold mb-1">Welcome</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Pick a username to save your portfolio. No password needed.
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400 mt-2">
            Note: anyone who knows your username can read or change your portfolio.
            Pick something only you would think of.
          </p>
        </div>
        <input
          autoFocus
          required
          minLength={2}
          maxLength={40}
          pattern="^[a-zA-Z0-9_.-]+$"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="username"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {error && (
          <p className="text-sm text-red-600 break-words">{error}</p>
        )}
        <button
          type="submit"
          disabled={submitting || value.trim().length < 2}
          className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {submitting ? "Saving..." : "Continue"}
        </button>
      </form>
    </div>
  )
}
