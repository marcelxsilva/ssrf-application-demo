import { C } from '../../../theme/tokens'
import Note from '../../../components/Note'
import LayerTrace from '../../../components/LayerTrace'

// Resultado do teste do webhook: veredito, trilha das camadas e corpo bruto (view).
export default function TestResult({ result }) {
  const val = result.validation
  const req = result.request
  const isSecure = result.mode === 'secure'
  const blocked = val?.performed && val?.allowed === false
  const leaked = result.mode === 'vulnerable' && req?.reached

  return (
    <div style={{ marginBottom: 16 }}>
      {blocked && (
        <Note color={C.green} background={C.greenSoft}>
          <b>Bloqueado na {val.layer_name}</b> - nenhuma requisição de saída foi feita. <span style={{ opacity: 0.85 }}>{val.reason}</span>
        </Note>
      )}
      {leaked && (
        <Note color={C.red} background={C.redSoft}>
          <b>SSRF bem-sucedido</b> - o servidor alcançou o destino interno e retornou a resposta ({req.status_code}).
        </Note>
      )}
      {isSecure && val?.allowed && (
        <Note color={C.green} background={C.greenSoft}>
          <b>URL aprovada nas 3 camadas</b> - destino na allowlist ({val.details?.matched_allow}).
        </Note>
      )}

      {isSecure && val?.performed && <LayerTrace layer={val.blocked_by_layer} />}

      <div style={{ marginTop: 10, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, overflow: 'hidden' }}>
        <div style={{ background: '#f9fafb', borderBottom: `1px solid ${C.border}`, padding: '9px 14px', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {req?.status_code && (
            <span style={{ background: req.status_code < 300 ? C.green : '#ea580c', color: '#fff', borderRadius: 6, padding: '1px 9px', fontWeight: 700, fontSize: 12.5 }}>{req.status_code}</span>
          )}
          <span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12, color: C.muted, flex: 1, wordBreak: 'break-all' }}>{result.url}</span>
          {req?.elapsed_ms && <span style={{ fontSize: 12, color: C.muted }}>{req.elapsed_ms} ms</span>}
        </div>
        <pre style={{ margin: 0, padding: 14, fontFamily: 'ui-monospace,monospace', fontSize: 12.5, color: leaked ? C.red : '#374151', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 300, overflowY: 'auto', background: '#fcfcfd' }}>
          {req?.body ? req.body : req?.detail ? `⚠  ${req.detail}` : '(sem conteúdo)'}
        </pre>
      </div>
    </div>
  )
}
