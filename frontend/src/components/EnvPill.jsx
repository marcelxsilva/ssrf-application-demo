import { C } from '../theme/tokens'

// Selo indicando o ambiente atual (seguro/vulnerável).
export default function EnvPill({ mode }) {
  const secure = mode === 'secure'
  return (
    <span style={{
      fontSize: 11, fontWeight: 700,
      color: secure ? C.green : C.red,
      background: secure ? C.greenSoft : C.redSoft,
      padding: '3px 10px', borderRadius: 999,
    }}>
      {secure ? 'seguro' : 'vulnerável'}
    </span>
  )
}
