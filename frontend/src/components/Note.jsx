// Caixa de destaque colorida (aviso/veredito).
export default function Note({ children, color, background }) {
  return (
    <div style={{
      background, border: `1px solid ${color}`, borderLeft: `3px solid ${color}`,
      borderRadius: 8, padding: '11px 14px', color, fontSize: 13.5, marginBottom: 4,
    }}>
      {children}
    </div>
  )
}
