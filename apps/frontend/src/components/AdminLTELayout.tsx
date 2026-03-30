import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type { Module } from './AdminLTEApp'
import { AdminLTEHome } from './AdminLTEHome'
import { DashboardPage } from '../pages/DashboardPage'
import { GeneratePage } from '../pages/GeneratePage'
import { BusinessPage } from '../pages/BusinessPage'
import { HistoryPage } from '../pages/HistoryPage'
import { AgentPage } from '../pages/AgentPage'
import { CalendarPage } from '../pages/CalendarPage'
import { StrategyPage } from '../pages/StrategyPage'
import { AdsPage } from '../pages/AdsPage'
import { DesignerPage } from '../pages/DesignerPage'
import { FinancePage } from '../pages/FinancePage'
import { AgencyPage } from '../pages/AgencyPage'
import { OnboardingPage } from '../pages/OnboardingPage'
import { api } from '../services/api'

export function AdminLTELayout() {
  const { usuario, logout } = useAuth()
  const [modulo, setModulo] = useState<Module>('home')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true')
  const [pendingCount, setPendingCount] = useState(0)
  const [onboardingBusinessId, setOnboardingBusinessId] = useState('')

  useEffect(() => {
    const classes = 'hold-transition sidebar-mini layout-fixed' + (darkMode ? ' dark-mode' : '')
    document.body.className = classes
    localStorage.setItem('darkMode', String(darkMode))
  }, [darkMode])

  // Busca pendentes a cada 60s
  useEffect(() => {
    function fetchPending() {
      api.listDrafts('pending_approval')
        .then(d => setPendingCount(d.length))
        .catch(() => {})
    }
    fetchPending()
    const timer = setInterval(fetchPending, 60_000)
    return () => clearInterval(timer)
  }, [])

  const navigate = (m: Module, data?: { businessId?: string }) => {
    if (m === 'onboarding' && data?.businessId) {
      setOnboardingBusinessId(data.businessId)
    }
    setModulo(m)
    if (m === 'dashboard') setPendingCount(0)
  }

  // Evento global de navegação (usado por páginas filhas)
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (typeof detail === 'string') {
        navigate(detail as Module)
      } else if (detail?.module) {
        navigate(detail.module as Module, detail)
      }
    }
    window.addEventListener('navigate', handler)
    return () => window.removeEventListener('navigate', handler)
  }, [])

  const PAGE_TITLES: Record<Module, string> = {
    home: 'Início',
    agency: 'Criar Conteúdo',
    dashboard: 'Revisar & Aprovar',
    generate: 'Gerar Rápido',
    businesses: 'Meus Negócios',
    history: 'Histórico',
    agent: 'Social Media',
    calendar: 'Calendário',
    strategy: 'Estratégia & Marca',
    ads: 'Google Ads',
    designer: 'Designer Visual',
    finance: 'Financeiro',
    onboarding: 'Configurar Negócio',
  }

  function renderModulo() {
    switch (modulo) {
      case 'home':      return <AdminLTEHome onNavigate={navigate} />
      case 'dashboard': return <DashboardPage />
      case 'generate':  return <GeneratePage />
      case 'businesses':return <BusinessPage />
      case 'history':   return <HistoryPage />
      case 'agent':     return <AgentPage />
      case 'calendar':  return <CalendarPage />
      case 'strategy':  return <StrategyPage />
      case 'ads':       return <AdsPage />
      case 'designer':  return <DesignerPage />
      case 'finance':   return <FinancePage />
      case 'agency':    return <AgencyPage />
      case 'onboarding': return <OnboardingPage businessId={onboardingBusinessId} onComplete={() => navigate('agency')} />
      default:          return <AdminLTEHome onNavigate={navigate} />
    }
  }

  const initials = usuario?.nome
    ?.split(' ')
    .slice(0, 2)
    .map(n => n[0])
    .join('')
    .toUpperCase() ?? 'U'

  function NavItem({ m, icon, label, badge }: { m: Module; icon: string; label: string; badge?: number }) {
    return (
      <li className="nav-item">
        <a
          href="#"
          className={`nav-link ${modulo === m ? 'active' : ''}`}
          onClick={e => { e.preventDefault(); navigate(m) }}
        >
          <i className={`nav-icon ${icon}`} />
          <p>
            {label}
            {badge != null && badge > 0 && (
              <span className="badge badge-warning right">{badge}</span>
            )}
          </p>
        </a>
      </li>
    )
  }

  return (
    <div className="wrapper">
      {/* Navbar */}
      <nav className="main-header navbar navbar-expand navbar-white navbar-light">
        <ul className="navbar-nav">
          <li className="nav-item">
            <a className="nav-link" data-widget="pushmenu" href="#" role="button">
              <i className="fas fa-bars" />
            </a>
          </li>
          {/* Breadcrumb do módulo atual */}
          <li className="nav-item d-none d-sm-block">
            <span className="nav-link text-muted" style={{ fontSize: 13 }}>
              {PAGE_TITLES[modulo]}
            </span>
          </li>
        </ul>

        <ul className="navbar-nav ml-auto align-items-center">
          {/* Pendentes */}
          {pendingCount > 0 && (
            <li className="nav-item">
              <button
                className="nav-link btn btn-link position-relative"
                title={`${pendingCount} post(s) aguardando aprovação`}
                onClick={() => navigate('dashboard')}
              >
                <i className="fas fa-bell" />
                <span
                  className="badge badge-danger navbar-badge"
                  style={{ fontSize: 9 }}
                >
                  {pendingCount}
                </span>
              </button>
            </li>
          )}

          {/* Dark mode */}
          <li className="nav-item">
            <button
              className="nav-link btn btn-link"
              title={darkMode ? 'Modo claro' : 'Modo escuro'}
              onClick={() => setDarkMode(d => !d)}
            >
              <i className={`fas ${darkMode ? 'fa-sun' : 'fa-moon'}`} />
            </button>
          </li>

          {/* Avatar + dropdown */}
          <li className="nav-item dropdown">
            <a className="nav-link d-flex align-items-center" data-toggle="dropdown" href="#" style={{ gap: 8 }}>
              <div
                style={{
                  width: 30, height: 30, borderRadius: '50%',
                  background: 'linear-gradient(135deg,#667eea,#764ba2)',
                  color: '#fff', fontSize: 12, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {initials}
              </div>
              <span className="d-none d-md-inline" style={{ fontSize: 13, fontWeight: 500 }}>
                {usuario?.nome?.split(' ')[0]}
              </span>
              <i className="fas fa-chevron-down" style={{ fontSize: 10 }} />
            </a>
            <div className="dropdown-menu dropdown-menu-right">
              <div className="dropdown-item-text">
                <div style={{ fontWeight: 600, fontSize: 14 }}>{usuario?.nome}</div>
                <div style={{ fontSize: 12, color: '#888' }}>{usuario?.email}</div>
              </div>
              <div className="dropdown-divider" />
              <button className="dropdown-item" onClick={logout}>
                <i className="fas fa-sign-out-alt mr-2 text-danger" />
                Sair
              </button>
            </div>
          </li>
        </ul>
      </nav>

      {/* Sidebar */}
      <aside className="main-sidebar sidebar-dark-primary elevation-4">
        <a href="#" className="brand-link" onClick={e => { e.preventDefault(); navigate('home') }}>
          <div
            style={{
              width: 30, height: 30, borderRadius: 8,
              background: 'linear-gradient(135deg,#667eea,#764ba2)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              marginRight: 8, flexShrink: 0,
            }}
          >
            <i className="fab fa-instagram" style={{ fontSize: 14, color: '#fff' }} />
          </div>
          <span className="brand-text font-weight-bold">Assistente Social</span>
        </a>

        {/* Mini avatar no sidebar */}
        <div className="sidebar">
          <div className="user-panel mt-3 pb-3 mb-3 d-flex">
            <div className="image">
              <div
                style={{
                  width: 34, height: 34, borderRadius: '50%',
                  background: 'linear-gradient(135deg,#667eea,#764ba2)',
                  color: '#fff', fontSize: 13, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >
                {initials}
              </div>
            </div>
            <div className="info">
              <span className="d-block" style={{ color: '#c2c7d0', fontWeight: 600, fontSize: 13 }}>
                {usuario?.nome?.split(' ')[0]}
              </span>
              <span style={{ color: '#6c757d', fontSize: 11 }}>Online</span>
            </div>
          </div>

          <nav className="mt-2">
            <ul className="nav nav-pills nav-sidebar flex-column" data-widget="treeview" role="menu">
              <NavItem m="home" icon="fas fa-home" label="Início" />

              {/* Ação principal — destaque visual */}
              <li className="nav-item">
                <a
                  href="#"
                  className={`nav-link ${modulo === 'agency' ? 'active' : ''}`}
                  onClick={e => { e.preventDefault(); navigate('agency') }}
                  style={modulo === 'agency'
                    ? { background: '#6f42c1' }
                    : { background: 'rgba(111,66,193,0.15)', borderLeft: '3px solid #6f42c1' }}
                >
                  <i className="nav-icon fas fa-magic" style={{ color: modulo === 'agency' ? '#fff' : '#6f42c1' }} />
                  <p style={{ fontWeight: 600, color: modulo === 'agency' ? '#fff' : '#c2c7d0' }}>Criar Conteúdo</p>
                </a>
              </li>

              <NavItem m="dashboard" icon="fas fa-check-double" label="Revisar & Aprovar" badge={pendingCount} />
              <NavItem m="calendar" icon="fas fa-calendar-alt" label="Calendário" />
              <NavItem m="history" icon="fas fa-history" label="Histórico" />

              {/* Configurações — colapsável */}
              <li className={`nav-item has-treeview ${['strategy', 'businesses', 'finance'].includes(modulo) ? 'menu-open' : ''}`}>
                <a href="#" className="nav-link" onClick={e => e.preventDefault()}>
                  <i className="nav-icon fas fa-cog" />
                  <p>Configurações <i className="fas fa-angle-left right" /></p>
                </a>
                <ul className="nav nav-treeview">
                  <NavItem m="strategy" icon="fas fa-chess" label="Estratégia & Marca" />
                  <NavItem m="businesses" icon="fas fa-building" label="Meus Negócios" />
                  <NavItem m="finance" icon="fas fa-wallet" label="Financeiro" />
                </ul>
              </li>

              {/* Especialistas — colapsável */}
              <li className={`nav-item has-treeview ${['agent', 'designer', 'ads', 'generate'].includes(modulo) ? 'menu-open' : ''}`}>
                <a href="#" className="nav-link" onClick={e => e.preventDefault()}>
                  <i className="nav-icon fas fa-users-cog" />
                  <p>Especialistas <i className="fas fa-angle-left right" /></p>
                </a>
                <ul className="nav nav-treeview">
                  <NavItem m="agent" icon="fas fa-share-alt" label="Social Media" />
                  <NavItem m="designer" icon="fas fa-palette" label="Designer Visual" />
                  <NavItem m="ads" icon="fas fa-ad" label="Google Ads" />
                  <NavItem m="generate" icon="fas fa-bolt" label="Gerar Rápido" />
                </ul>
              </li>
            </ul>
          </nav>
        </div>
      </aside>

      {/* Content */}
      <div className="content-wrapper">
        <div className="content-header">
          <div className="container-fluid">
            <div className="row mb-2">
              <div className="col-sm-6">
                <h1 className="m-0">{PAGE_TITLES[modulo]}</h1>
              </div>
            </div>
          </div>
        </div>
        <section className="content">
          <div className="container-fluid">
            {renderModulo()}
          </div>
        </section>
      </div>

      <footer className="main-footer">
        <strong>Assistente Multimídia Social</strong> — Todos os direitos reservados.
      </footer>
    </div>
  )
}
