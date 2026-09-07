// Camada de acesso à API do FinanceHub. Concentra todas as chamadas HTTP;
// nenhum componente fala com fetch diretamente.

const API = '/api'

async function request(path, { method = 'GET', token, body } = {}) {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${API}${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  })
  return res
}

export async function apiLogin(username, password) {
  const res = await request('/auth/login', { method: 'POST', body: { username, password } })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Falha no login')
  }
  return res.json()
}

async function json(res) {
  if (!res.ok) throw new Error(String(res.status))
  return res.json()
}

// --- endpoints de domínio ---
export const getMe = (token) => request('/me', { token }).then(json)
export const getTransactions = (token) => request('/transactions', { token }).then(json)
export const getConfig = () => request('/config').then(json)
export const getWebhook = (token) => request('/webhook', { token }).then(json)

export const testWebhook = (mode, token, url) =>
  request(`/${mode}/webhook/test`, { method: 'POST', token, body: { url } }).then((r) => r.json())

export const saveWebhook = (mode, token, url) =>
  request(`/${mode}/webhook/save`, { method: 'POST', token, body: { url } }).then((r) => r.json())
