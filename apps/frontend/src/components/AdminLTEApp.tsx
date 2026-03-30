import { AdminLTELayout } from './AdminLTELayout'
import { AdminLTEHome } from './AdminLTEHome'

export type Module = 'home' | 'dashboard' | 'generate' | 'businesses' | 'history' | 'agent' | 'calendar' | 'strategy' | 'ads' | 'designer' | 'finance' | 'agency' | 'onboarding'

export function AdminLTEApp() {
  return <AdminLTELayout />
}

export { AdminLTEHome }
