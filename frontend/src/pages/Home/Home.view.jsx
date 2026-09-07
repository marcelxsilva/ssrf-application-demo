import { C, btnGhost } from '../../theme/tokens'
import EnvPill from '../../components/EnvPill'
import Tab from '../../components/Tab'

// Layout da área logada (cabeçalho + conteúdo). Presentational: recebe o conteúdo
// da aba atual via `children` e delega ações por callbacks.
export default function HomeView({ mode, user, tab, onNavigate, onLogout, children }) {
  return (
    <div>
      <header style={{ background: C.card, borderBottom: `1px solid ${C.border}`, padding: '0 28px', display: 'flex', alignItems: 'center', gap: 8, height: 60 }}>
        <div style={{ fontWeight: 800, fontSize: 18, color: C.blue, marginRight: 6 }}>FinanceHub</div>
        <EnvPill mode={mode} />
        <div style={{ width: 14 }} />
        <Tab active={tab === 'dashboard'} onClick={() => onNavigate(`/${mode}`)} label="Início" />
        <Tab active={tab === 'webhooks'} onClick={() => onNavigate(`/${mode}/webhooks`)} label="Webhooks" />
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: 14, color: C.muted }}>{user.full_name}</span>
          <button onClick={onLogout} style={{ ...btnGhost, padding: '7px 14px' }}>Sair</button>
        </div>
      </header>
      <main style={{ maxWidth: 1040, margin: '0 auto', padding: '28px 22px 64px' }}>
        {children}
      </main>
    </div>
  )
}
