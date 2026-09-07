import LandingView from './Landing.view'

// Container da página inicial: mapeia a escolha para a rota da aplicação.
export default function Landing({ navigate }) {
  return <LandingView onSelect={(mode) => navigate(`/${mode}`)} />
}
