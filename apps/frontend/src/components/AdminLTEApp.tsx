import { useAuth } from '../contexts/AuthContext'
import { AdminLTELayout } from './AdminLTELayout'
import { AdminLTEHome } from './AdminLTEHome'

export type Module = 'home'
// Adicionar novos módulos: 'home' | 'clientes' | 'documentos' | 'meu-modulo'

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

function LoginPage({ onLogin }: { readonly onLogin: (token: string) => Promise<void> }) {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string

  function handleCredential(response: { credential: string }) {
    onLogin(response.credential).catch(console.error)
  }

  return (
    <div className="hold-transition login-page">
      <div className="login-box">
        <div className="login-logo">
          <strong>Meu Projeto</strong>
        </div>
        <div className="card">
          <div className="card-body login-card-body text-center">
            <p className="login-box-msg">Faça login para continuar</p>
            <div
              id="g_id_onload"
              data-client_id={clientId}
              data-callback="handleGoogleLogin"
              data-auto_prompt="false"
            />
            <div
              className="g_id_signin"
              data-type="standard"
              data-size="large"
              data-theme="outline"
              data-text="sign_in_with"
              data-shape="rectangular"
              data-logo_alignment="left"
            />
          </div>
        </div>
      </div>
      <script
        dangerouslySetInnerHTML={{
          __html: `window.handleGoogleLogin = ${handleCredential.toString()}`,
        }}
      />
    </div>
  )
}

export { AdminLTEHome }
