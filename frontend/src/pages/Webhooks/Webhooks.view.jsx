import { C, btn, btnGhost, accentFor } from '../../theme/tokens'
import Deliveries from './components/Deliveries'
import TestResult from './components/TestResult'

// Camada visual da página de webhooks. Sem regra de negócio: recebe estado e callbacks.
export default function WebhooksView({
  mode, url, onUrlChange, onTest, onSave,
  loading, config, saveMessage, result, webhook,
}) {
  const isVuln = mode === 'vulnerable'
  const accent = accentFor(mode)
  const disabled = loading || !url.trim()

  return (
    <div>
      <h2 style={{ fontSize: 18, margin: 0 }}>Webhooks</h2>
      <p style={{ fontSize: 13.5, color: C.muted, margin: '2px 0 14px' }}>
        Cadastre uma URL para receber notificações das suas movimentações. O servidor testa a URL antes de salvar.
      </p>

      <div style={{ background: isVuln ? C.redSoft : C.greenSoft, border: `1px solid ${accent}33`, borderLeft: `3px solid ${accent}`, borderRadius: 8, padding: '10px 14px', fontSize: 13, color: isVuln ? C.red : C.green, marginBottom: 16 }}>
        {isVuln
          ? 'Versão vulnerável: o servidor requisita/entrega para qualquer URL, sem validar o destino - SSRF explorável.'
          : 'Versão segura: toda URL passa por 3 camadas de validação antes de qualquer requisição de saída.'}
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
        <input
          value={url} onChange={(e) => onUrlChange(e.target.value)}
          placeholder="https://hooks.parceiro-financehub.com/eventos"
          style={{ flex: 1, background: '#fff', border: `1px solid ${C.border}`, borderRadius: 8, padding: '11px 14px', fontSize: 14.5, fontFamily: 'ui-monospace,monospace', color: C.text }}
          onFocus={(e) => (e.target.style.borderColor = accent)}
          onBlur={(e) => (e.target.style.borderColor = C.border)}
        />
        <button onClick={onTest} disabled={disabled} style={{ ...btnGhost, opacity: disabled ? 0.5 : 1 }}>Testar</button>
        <button onClick={onSave} disabled={disabled} style={btn(accent, false, disabled)}>Salvar</button>
      </div>

      {config && !isVuln && (
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 12 }}>
          Allowlist: {config.allowlist.map((d, i) => (
            <code key={d} style={{ color: C.green }}>{d}{i < config.allowlist.length - 1 ? ', ' : ''}</code>
          ))} · timeout {config.outbound_timeout_seconds}s · redirects off
        </div>
      )}

      {saveMessage && (
        <div style={{ background: saveMessage.ok ? C.greenSoft : C.redSoft, border: `1px solid ${saveMessage.ok ? C.green : C.red}`, color: saveMessage.ok ? C.green : C.red, borderRadius: 8, padding: '11px 14px', fontSize: 13.5, marginBottom: 14 }}>
          {saveMessage.text}
        </div>
      )}

      {result && <TestResult result={result} />}

      <Deliveries webhook={webhook} />
    </div>
  )
}
