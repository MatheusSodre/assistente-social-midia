import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './contexts/AuthContext'
import { AdminLTEApp } from './components/AdminLTEApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <AdminLTEApp />
    </AuthProvider>
  </StrictMode>,
)
