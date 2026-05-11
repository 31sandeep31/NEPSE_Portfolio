import { useEffect, useState } from "react"

const STORAGE_KEY = "nepse_portfolio_username_v1"

export function useUsername() {
  const [username, setUsernameState] = useState<string | null>(() => {
    if (typeof window === "undefined") return null
    return window.localStorage.getItem(STORAGE_KEY)
  })

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setUsernameState(e.newValue)
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  const setUsername = (next: string | null) => {
    if (next) window.localStorage.setItem(STORAGE_KEY, next)
    else window.localStorage.removeItem(STORAGE_KEY)
    setUsernameState(next)
  }

  return { username, setUsername }
}
