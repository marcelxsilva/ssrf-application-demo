import { C, btn } from '../../theme/tokens'
import EnvPill from '../../components/EnvPill'
import Field from '../../components/Field'

// Camada visual do login: só recebe estado e callbacks, sem regra de negócio.
export default function LoginView({
  mode, username, password, error, loading,
  onUsernameChange, onPasswordChange, onSubmit, onSwitchVersion,
}) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: 380, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 34, boxShadow: '0 4px 24px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontWeight: 800, fontSize: 22, color: C.blue }}>FinanceHub</div>
          <EnvPill mode={mode} />
        </div>
        <p style={{ color: C.muted, fontSize: 14, margin: '8px 0 22px' }}>Acesse sua conta</p>
        <form onSubmit={onSubmit}>
          <Field label="Usuário" value={username} onChange={onUsernameChange} placeholder="joao" />
          <Field label="Senha" type="password" value={password} onChange={onPasswordChange} placeholder="••••••" />
          {error && (
            <div style={{ background: C.redSoft, border: `1px solid ${C.red}`, color: C.red, borderRadius: 8, padding: '9px 12px', fontSize: 13, marginBottom: 14 }}>{error}</div>
          )}
          <button disabled={loading} style={btn(C.blue, true, loading)}>{loading ? 'Entrando...' : 'Entrar'}</button>
        </form>
        <div style={{ marginTop: 18, paddingTop: 14, borderTop: `1px solid ${C.border}`, fontSize: 12.5, color: C.muted, display: 'flex', justifyContent: 'flex-end' }}>
          <a onClick={onSwitchVersion} style={{ cursor: 'pointer', color: C.blue }}>trocar versão</a>
        </div>
      </div>
    </div>
  )
}
