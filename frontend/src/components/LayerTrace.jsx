import { C } from '../theme/tokens'

const LAYERS = [
  { n: 1, name: 'Esquema/estrutura' },
  { n: 2, name: 'DNS e IP' },
  { n: 3, name: 'Allowlist' },
]

// Trilha visual das 3 camadas de validação, destacando onde bloqueou.
export default function LayerTrace({ layer }) {
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
      {LAYERS.map((l) => {
        let state = 'pass'
        if (layer === l.n) state = 'block'
        else if (layer && l.n > layer) state = 'skip'
        const c = state === 'block'
          ? { bg: C.redSoft, bd: C.red, fg: C.red, ic: '✕' }
          : state === 'skip'
            ? { bg: '#f9fafb', bd: C.border, fg: '#9ca3af', ic: '–' }
            : { bg: C.greenSoft, bd: C.green, fg: C.green, ic: '✓' }
        return (
          <div key={l.n} style={{ flex: 1, background: c.bg, border: `1px solid ${c.bd}`, borderRadius: 8, padding: '8px 11px' }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 700 }}>CAMADA {l.n} {c.ic}</div>
            <div style={{ fontSize: 12, color: c.fg, marginTop: 2 }}>{l.name}</div>
          </div>
        )
      })}
    </div>
  )
}
