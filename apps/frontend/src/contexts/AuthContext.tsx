import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { API_BASE } from '../services/api'

interface Usuario {
  id: string
  nome: string
  email: string
  telefone: string | null
  plano: string
  role: string
}

interface AuthContextValue {
  usuario: Usuario | null
  token: string | null
  loading: boolean
  login: (googleToken: string) => Promise<void>
  logout: () => void
  authHeader: () => Record<string, string>
}

const AuthContext = createContext<AuthContextValue | null>(null)

const JWT_KEY = 'aa_jwt'

export function AuthProvider({ children }: { readonly children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem(JWT_KEY)
    if (saved) {
      setToken(saved)
      fetchMe(saved)
        .then(setUsuario)
        .catch(() => localStorage.removeItem(JWT_KEY))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  async function fetchMe(jwt: string): Promise<Usuario> {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${jwt}` },
    })
    if (!res.ok) throw new Error('Unauthorized')
    return res.json() as Promise<Usuario>
  }

  async function login(googleToken: string) {
    const res = await fetch(`${API_BASE}/api/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: googleToken }),
    })
    if (!res.ok) throw new Error('Login falhou')
    const data = (await res.json()) as { access_token: string; usuario: Usuario }
    localStorage.setItem(JWT_KEY, data.access_token)
    setToken(data.access_token)
    setUsuario(data.usuario)
  }

  function logout() {
    localStorage.removeItem(JWT_KEY)
    setToken(null)
    setUsuario(null)
  }

  function authHeader(): Record<string, string> {
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  return (
    <AuthContext.Provider value={{ usuario, token, loading, login, logout, authHeader }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}
