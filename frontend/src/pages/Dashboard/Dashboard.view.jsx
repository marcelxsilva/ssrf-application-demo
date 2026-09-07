import { C } from '../../theme/tokens'
import { brl } from '../../utils/format'

// Camada visual do dashboard: saldo e lista de movimentações do usuário.
export default function DashboardView({ user, data }) {
  return (
    <div>
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: '22px 24px', marginBottom: 22 }}>
        <div style={{ fontSize: 13, color: C.muted }}>Conta {user.account_number} · {user.full_name}</div>
        <div style={{ fontSize: 32, fontWeight: 800, marginTop: 4 }}>{data ? brl(data.balance) : '-'}</div>
        <div style={{ fontSize: 13, color: C.muted }}>Saldo disponível</div>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
        <h2 style={{ fontSize: 16, margin: 0 }}>Suas movimentações</h2>
        <span style={{ fontSize: 12, color: C.muted }}>· atualiza automaticamente</span>
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}>
        {data?.transactions?.map((t) => (
          <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '13px 18px', borderBottom: `1px solid ${C.border}` }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: t.amount >= 0 ? C.greenSoft : C.redSoft, color: t.amount >= 0 ? C.green : C.red, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>{t.amount >= 0 ? '↑' : '↓'}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14 }}>{t.description}</div>
              <div style={{ fontSize: 12, color: C.muted }}>{new Date(t.date).toLocaleDateString('pt-BR')} · {t.kind}</div>
            </div>
            <div style={{ fontWeight: 700, color: t.amount >= 0 ? C.green : C.red }}>{brl(t.amount)}</div>
          </div>
        ))}
        {!data && <div style={{ padding: 20, color: C.muted }}>Carregando...</div>}
      </div>

      <p style={{ fontSize: 12.5, color: C.muted, marginTop: 12 }}>
        Você só enxerga as movimentações da sua própria conta - a autorização é validada no servidor.
      </p>
    </div>
  )
}
