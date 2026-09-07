import { useAuth } from '../../hooks/useAuth'
import Login from '../Login'
import Dashboard from '../Dashboard'
import Webhooks from '../Webhooks'
import HomeView from './Home.view'

// Container de uma aplicação (modo). Faz o gate de autenticação e resolve a aba
// atual a partir da rota, montando o conteúdo correspondente.
export default function Home({ mode, path, navigate }) {
  const { token, user, authenticated, login, logout } = useAuth(mode)

  if (!authenticated) {
    return (
      <Login
        mode={mode}
        navigate={navigate}
        onLogin={(data) => { login(data); navigate(`/${mode}`) }}
      />
    )
  }

  const tab = path.startsWith(`/${mode}/webhooks`) ? 'webhooks' : 'dashboard'

  return (
    <HomeView
      mode={mode}
      user={user}
      tab={tab}
      onNavigate={navigate}
      onLogout={() => { logout(); navigate(`/${mode}/login`) }}
    >
      {tab === 'dashboard'
        ? <Dashboard user={user} token={token} />
        : <Webhooks token={token} mode={mode} />}
    </HomeView>
  )
}
