import { type FormEvent, useState } from 'react'
import { supabase } from '../lib/supabase'
import { Sprite } from './Sprite'

const INVALID_CREDENTIALS = 'Invalid login credentials'

function friendlyError(message: string) {
  return message === INVALID_CREDENTIALS ? 'Usuario o contraseña incorrectos' : message
}

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password })
    setError(signInError ? friendlyError(signInError.message) : null)
    setLoading(false)
  }

  return (
    <div className="welcome">
      <div className="welcome__hero">
        <Sprite scale={3} animate />
        <h1 className="welcome__title">Nailong</h1>
      </div>

      <form className="login" onSubmit={handleSubmit}>
        <label className="field">
          <span className="field__label">Usuario</span>
          <input
            type="email"
            placeholder="tu@nailong.app"
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            inputMode="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">Contraseña</span>
          <div className="field__control">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button type="button" className="field__toggle" onClick={() => setShowPassword((visible) => !visible)}>
              {showPassword ? 'Ocultar' : 'Ver'}
            </button>
          </div>
        </label>

        {error && <p className="error" role="alert">{error}</p>}

        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Entrando…' : 'Entrar a casa'}
        </button>
      </form>
    </div>
  )
}
