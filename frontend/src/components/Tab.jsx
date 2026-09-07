import { C } from '../theme/tokens'

// Aba de navegação do cabeçalho.
export default function Tab({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'none', border: 'none',
        borderBottom: active ? `2px solid ${C.blue}` : '2px solid transparent',
        color: active ? C.text : C.muted,
        padding: '20px 12px', fontSize: 14.5, fontWeight: active ? 700 : 500,
        cursor: 'pointer', height: 60,
      }}
    >
      {label}
    </button>
  )
}
