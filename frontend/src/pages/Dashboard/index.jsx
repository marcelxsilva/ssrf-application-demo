import { useState, useEffect, useCallback } from 'react'
import { getTransactions } from '../../services/api'
import DashboardView from './Dashboard.view'

const REFRESH_MS = 8000

// Container do dashboard: busca as transações e mantém a lista atualizada.
export default function Dashboard({ user, token }) {
  const [data, setData] = useState(null)

  const load = useCallback(() => {
    getTransactions(token).then(setData).catch(() => {})
  }, [token])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [load])

  return <DashboardView user={user} data={data} />
}
