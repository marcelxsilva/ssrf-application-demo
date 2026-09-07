import { C } from '../../theme/tokens'

const OPTIONS = [
  {
    mode: 'vulnerable', badge: 'VULNERÁVEL', title: 'Versão vulnerável',
    desc: 'Aplicação sem validação de URL no webhook. Permite explorar o SSRF e alcançar a rede interna.',
    color: C.red, soft: C.redSoft,
  },
  {
    mode: 'secure', badge: 'CORRIGIDO', title: 'Versão segura',
    desc: 'Mesma aplicação com o validador de 3 camadas. Os destinos internos são bloqueados.',
    color: C.green, soft: C.greenSoft,
  },
]

// Apresentação da página inicial: escolha da versão da aplicação.
export default function LandingView({ onSelect }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, gap: 28 }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontWeight: 800, fontSize: 26, color: C.blue }}>FinanceHub</div>
        <p style={{ color: C.muted, fontSize: 14, margin: '6px 0 0' }}>Demonstração de SSRF - escolha a versão da aplicação</p>
      </div>
      <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap', justifyContent: 'center' }}>
        {OPTIONS.map((o) => (
          <button key={o.mode} onClick={() => onSelect(o.mode)} style={{ textAlign: 'left', background: C.card, border: `1px solid ${C.border}`, borderTop: `4px solid ${o.color}`, borderRadius: 14, padding: 26, cursor: 'pointer', width: 320, boxShadow: '0 4px 20px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'inline-block', fontSize: 12, fontWeight: 700, color: o.color, background: o.soft, padding: '3px 10px', borderRadius: 999, marginBottom: 12 }}>{o.badge}</div>
            <h3 style={{ margin: '0 0 6px', fontSize: 19 }}>{o.title}</h3>
            <p style={{ margin: 0, fontSize: 13.5, color: C.muted, lineHeight: 1.5 }}>{o.desc}</p>
            <div style={{ marginTop: 16, fontSize: 13, fontWeight: 600, color: o.color }}>{`/${o.mode}`} →</div>
          </button>
        ))}
      </div>
      <p style={{ color: C.muted, fontSize: 12.5 }}>Contas: <b>joao</b>, <b>maria</b>, <b>ana</b> - senha <b>senha123</b></p>
    </div>
  )
}
