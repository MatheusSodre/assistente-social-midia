import { useState, useEffect } from 'react'
import { AdminLTELayout } from './AdminLTELayout'
import { AdminLTEHome } from './AdminLTEHome'
import { LandingPage } from '../pages/LandingPage'

export type Module = 'home' | 'dashboard' | 'generate' | 'businesses' | 'history' | 'agent' | 'calendar' | 'strategy' | 'ads' | 'designer' | 'finance' | 'agency' | 'onboarding'

export function AdminLTEApp() {
  const [view, setView] = useState<'landing' | 'app'>('app')

  const handleLogin = () => {
    localStorage.setItem('app_entered', 'true')
    setView('app')
  }

  // Expor função global para voltar à landing (logout)
  useEffect(() => {
    (window as any).__goToLanding = () => {
      localStorage.removeItem('app_entered')
      setView('landing')
    }
  }, [])

  if (view === 'landing') {
    return <LandingPage onLogin={handleLogin} />
  }

  return <AdminLTELayout />
}

export { AdminLTEHome }
