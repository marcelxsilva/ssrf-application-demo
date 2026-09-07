import { useState, useEffect, useCallback } from 'react'
import { getConfig, getWebhook, testWebhook, saveWebhook } from '../../services/api'
import WebhooksView from './Webhooks.view'

const REFRESH_MS = 6000

// Container da página de webhooks: concentra as regras (testar, salvar, atualizar
// as entregas e a configuração). A view apenas renderiza.
export default function Webhooks({ token, mode }) {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [saveMessage, setSaveMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState(null)
  const [webhook, setWebhook] = useState(null)

  const loadWebhook = useCallback(() => {
    getWebhook(token).then(setWebhook).catch(() => {})
  }, [token])

  useEffect(() => { getConfig().then(setConfig).catch(() => {}) }, [])

  useEffect(() => {
    loadWebhook()
    const id = setInterval(loadWebhook, REFRESH_MS)
    return () => clearInterval(id)
  }, [loadWebhook])

  const handleTest = async () => {
    if (!url.trim()) return
    setLoading(true); setResult(null); setSaveMessage(null)
    try {
      setResult(await testWebhook(mode, token, url))
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!url.trim()) return
    setLoading(true); setResult(null)
    try {
      const r = await saveWebhook(mode, token, url)
      setSaveMessage(r.saved
        ? { ok: true, text: 'Webhook salvo. As próximas transações serão entregues a ele.' }
        : { ok: false, text: `Não salvo - ${r.validation?.layer_name}: ${r.validation?.reason}` })
      loadWebhook()
    } finally {
      setLoading(false)
    }
  }

  return (
    <WebhooksView
      mode={mode}
      url={url}
      onUrlChange={setUrl}
      onTest={handleTest}
      onSave={handleSave}
      loading={loading}
      config={config}
      saveMessage={saveMessage}
      result={result}
      webhook={webhook}
    />
  )
}
