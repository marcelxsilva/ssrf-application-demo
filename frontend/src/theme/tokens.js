// Tokens visuais e helpers de estilo compartilhados (tema claro).

export const C = {
  bg: '#f5f6f8', card: '#ffffff', border: '#e5e7eb', text: '#1f2937', muted: '#6b7280',
  blue: '#2563eb', red: '#dc2626', green: '#16a34a',
  redSoft: '#fef2f2', greenSoft: '#f0fdf4', blueSoft: '#eff6ff',
}

export const btn = (color, full = false, disabled = false) => ({
  width: full ? '100%' : undefined,
  background: color, color: '#fff', border: 'none', borderRadius: 8,
  padding: '11px 18px', fontWeight: 600, fontSize: 15,
  cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1,
})

export const btnGhost = {
  background: '#fff', color: C.text, border: `1px solid ${C.border}`,
  borderRadius: 8, padding: '11px 16px', fontWeight: 600, fontSize: 14, cursor: 'pointer',
}

// Cor de destaque conforme o modo da aplicação.
export const accentFor = (mode) => (mode === 'secure' ? C.green : C.red)
