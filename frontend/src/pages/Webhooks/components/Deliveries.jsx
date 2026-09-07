import { C } from '../../../theme/tokens'
import { brl } from '../../../utils/format'

// Lista de entregas recentes do webhook (view).
export default function Deliveries({ webhook }) {
  return (
    <div style={{ marginTop: 20, background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '12px 16px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 8 }}>
        <b style={{ fontSize: 14 }}>Entregas recentes ao webhook</b>
        <span style={{ fontSize: 12, color: C.muted }}>· nova transação a cada 2 min</span>
      </div>

      {webhook?.webhook_url ? (
        <div style={{ padding: '8px 16px', fontSize: 12.5, color: C.muted, borderBottom: `1px solid ${C.border}`, fontFamily: 'ui-monospace,monospace' }}>
          destino: {webhook.webhook_url}
        </div>
      ) : (
        <div style={{ padding: 16, fontSize: 13, color: C.muted }}>
          Nenhum webhook cadastrado. Salve uma URL acima para começar a receber as transações.
        </div>
      )}

      {webhook?.deliveries?.map((d) => (
        <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', borderBottom: `1px solid ${C.border}` }}>
          <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 999, background: d.ok ? C.greenSoft : C.redSoft, color: d.ok ? C.green : C.red }}>
            {d.ok ? `entregue ${d.status_code || ''}` : (d.detail || 'falhou')}
          </span>
          <span style={{ flex: 1, fontSize: 13 }}>{d.description}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: d.amount >= 0 ? C.green : C.red }}>{brl(d.amount)}</span>
          <span style={{ fontSize: 12, color: C.muted, width: 62, textAlign: 'right' }}>{d.at}</span>
        </div>
      ))}

      {webhook?.webhook_url && !webhook?.deliveries?.length && (
        <div style={{ padding: 14, fontSize: 13, color: C.muted }}>Aguardando a próxima transação...</div>
      )}
    </div>
  )
}
