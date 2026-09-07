import { useState, useEffect, useCallback } from 'react'

// Router mínimo baseado em history/pathname (sem dependência externa).
export function useRouter() {
  const [path, setPath] = useState(window.location.pathname)

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = useCallback((to) => {
    window.history.pushState({}, '', to)
    setPath(to)
  }, [])

  return { path, navigate }
}

// Deriva o modo (aplicação) a partir do caminho.
export function modeFromPath(path) {
  if (path.startsWith('/secure')) return 'secure'
  if (path.startsWith('/vulnerable')) return 'vulnerable'
  return null
}
