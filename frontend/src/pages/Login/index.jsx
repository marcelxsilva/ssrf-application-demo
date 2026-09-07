import { useState } from 'react'
import { apiLogin } from '../../services/api'
import LoginView from './Login.view'

// Container do login: estado do formulário, submissão e tratamento de erro.
// A view não conhece a API - só recebe callbacks.
export default function Login({ mode, onLogin, navigate }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await apiLogin(username, password)
      onLogin(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <LoginView
      mode={mode}
      username={username}
      password={password}
      error={error}
      loading={loading}
      onUsernameChange={setUsername}
      onPasswordChange={setPassword}
      onSubmit={handleSubmit}
      onSwitchVersion={() => navigate('/')}
    />
  )
}
