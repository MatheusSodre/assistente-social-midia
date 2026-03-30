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

// Login com Google desabilitado por enquanto — usuário dev automático
const DEV_USUARIO: Usuario = {
  id: 'dev-user-001',
  nome: 'Dev User',
  email: 'dev@local.dev',
  telefone: null,
  plano: 'pro',
  role: 'admin',
}

export function AuthProvider({ children }: { readonly children: ReactNode }) {
  const [usuario] = useState<Usuario | null>(DEV_USUARIO)
  const [token] = useState<string | null>(null)
  const [loading] = useState(false)

  async function login(_googleToken: string) {
    // noop — login desabilitado
  }

  function logout() {
    // noop — login desabilitado
  }

  function authHeader(): Record<string, string> {
    return {}
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
