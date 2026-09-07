import { C } from '../theme/tokens'

// Campo de formulário rotulado.
export default function Field({ label, value, onChange, type = 'text', placeholder }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 13, color: C.muted, display: 'block', marginBottom: 6 }}>{label}</label>
      <input
        type={type} value={value} placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: '100%', background: '#fff', border: `1px solid ${C.border}`, borderRadius: 8, padding: '11px 13px', color: C.text, fontSize: 15 }}
        onFocus={(e) => (e.target.style.borderColor = C.blue)}
        onBlur={(e) => (e.target.style.borderColor = C.border)}
      />
    </div>
  )
}
