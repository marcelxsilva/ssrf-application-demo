import { C } from './theme/tokens'
import { useRouter, modeFromPath } from './hooks/useRouter'
import Landing from './pages/Landing'
import Home from './pages/Home'

// Router de topo: fora de /secure e /vulnerable mostra a landing; dentro, monta a
// aplicação daquele modo (contexto completo e isolado).
export default function App() {
  const { path, navigate } = useRouter()
  const mode = modeFromPath(path)

  return (
    <div style={{ minHeight: '100vh', background: C.bg, color: C.text, fontFamily: "'Inter','Segoe UI',system-ui,sans-serif" }}>
      {mode
        ? <Home key={mode} mode={mode} path={path} navigate={navigate} />
        : <Landing navigate={navigate} />}
    </div>
  )
}
