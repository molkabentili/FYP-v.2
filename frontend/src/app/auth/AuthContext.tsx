import { createContext, PropsWithChildren, useCallback, useContext, useMemo, useState } from 'react'
import { loginUser, type UserProfile } from '../../services/api'

type StoredAuth = {
  token: string
  user: UserProfile
}

type AuthContextValue = {
  token: string | null
  user: UserProfile | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AUTH_STORAGE_KEY = 'smartseg_auth'
const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function decodeTokenPayload(token: string): { exp?: number } | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null

    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    return JSON.parse(window.atob(padded))
  } catch {
    return null
  }
}

function isExpired(token: string) {
  const payload = decodeTokenPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 <= Date.now()
}

function readStoredAuth(): StoredAuth | null {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null

    const stored = JSON.parse(raw) as StoredAuth
    if (!stored.token || !stored.user || isExpired(stored.token)) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      return null
    }

    return stored
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [auth, setAuth] = useState<StoredAuth | null>(() => readStoredAuth())

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginUser(email, password)
    const nextAuth = {
      token: response.access_token,
      user: response.user,
    }

    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuth))
    setAuth(nextAuth)
  }, [])

  const logout = useCallback(() => {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    setAuth(null)
  }, [])

  const value = useMemo(
    () => ({
      token: auth?.token ?? null,
      user: auth?.user ?? null,
      isAuthenticated: Boolean(auth?.token && auth.user),
      login,
      logout,
    }),
    [auth, login, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
