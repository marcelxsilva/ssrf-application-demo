import { useState, useEffect, useCallback } from 'react'
import { getMe } from '../services/api'

// Autenticação por modo: cada aplicação (/secure e /vulnerable) tem seu token
// isolado no localStorage. Carrega o usuário atual a partir do token.
export function useAuth(mode) {
  const tokenKey = `fh_token_${mode}`
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) || '')
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (!token) { setUser(null); return }
    let active = true
    getMe(token)
      .then((u) => { if (active) setUser(u) })
      .catch(() => { setToken(''); localStorage.removeItem(tokenKey) })
    return () => { active = false }
  }, [token, tokenKey])

  const login = useCallback((data) => {
    localStorage.setItem(tokenKey, data.access_token)
    setToken(data.access_token)
  }, [tokenKey])

  const logout = useCallback(() => {
    localStorage.removeItem(tokenKey)
    setToken('')
    setUser(null)
  }, [tokenKey])

  return { token, user, authenticated: Boolean(token && user), login, logout }
}
