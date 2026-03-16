import { useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { AdminLTELayout } from './AdminLTELayout'
import { AdminLTEHome } from './AdminLTEHome'

export type Module = 'home' | 'dashboard' | 'generate' | 'businesses' | 'history' | 'agent' | 'calendar' | 'strategy' | 'ads' | 'designer'

export function AdminLTEApp() {
  const { usuario, loading, login } = useAuth()

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <div className="spinner-border text-primary" role="status" />
      </div>
    )
  }

  if (!usuario) {
    return <LoginPage onLogin={login} />
  }

  return <AdminLTELayout />
}

interface GoogleAccounts {
  accounts: {
    id: {
      initialize: (config: { client_id: string; callback: (r: { credential: string }) => void }) => void
      renderButton: (el: HTMLElement, opts: Record<string, string>) => void
    }
  }
}

function LoginPage({ onLogin }: { readonly onLogin: (token: string) => Promise<void> }) {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string

  // Inicializa o botão do Google — polling até o script carregar
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>

    function initGoogle() {
      const google = (window as unknown as { google?: GoogleAccounts }).google
      if (!google) return false

      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => onLogin(response.credential).catch(console.error),
      })

      const btn = document.getElementById('google-signin-btn')
      if (btn) {
        google.accounts.id.renderButton(btn, {
          type: 'standard',
          size: 'large',
          theme: 'outline',
          text: 'sign_in_with',
          shape: 'rectangular',
          logo_alignment: 'left',
        })
      }
      return true
    }

    if (!initGoogle()) {
      // polling a cada 200ms até o script do Google estar disponível
      timer = setInterval(() => {
        if (initGoogle()) clearInterval(timer)
      }, 200)
    }

    return () => clearInterval(timer)
  }, [clientId, onLogin])

  return (
    <div className="login-box">
      <div className="login-logo">
        <strong>Assistente Social Midia</strong>
      </div>
      <div className="card">
        <div className="card-body login-card-body text-center">
          <p className="login-box-msg">Faça login para continuar</p>
          <div id="google-signin-btn" />
        </div>
      </div>
    </div>
  )
}

export { AdminLTEHome }
