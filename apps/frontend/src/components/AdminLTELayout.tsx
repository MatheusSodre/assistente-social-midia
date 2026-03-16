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
import { api } from '../services/api'

export function AdminLTELayout() {
  const { usuario, logout } = useAuth()
  const [modulo, setModulo] = useState<Module>('home')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true')
  const [pendingCount, setPendingCount] = useState(0)

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

  const navigate = (m: Module) => {
    setModulo(m)
    if (m === 'dashboard') setPendingCount(0)
  }

  // Evento global de navegação (usado por páginas filhas)
  useEffect(() => {
    const handler = (e: Event) => navigate((e as CustomEvent).detail as Module)
    window.addEventListener('navigate', handler)
    return () => window.removeEventListener('navigate', handler)
  }, [])

  const PAGE_TITLES: Record<Module, string> = {
    home: 'Início',
    dashboard: 'Aprovação de Conteúdo',
    generate: 'Gerar Conteúdo',
    businesses: 'Meus Businesses',
    history: 'Histórico de Posts',
    agent: 'Agente Social — Mara',
    calendar: 'Calendário Editorial',
    strategy: 'Estratégia de Marca',
    ads: 'Google Ads — Luna',
    designer: 'Designer Visual — Pixel',
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

              <li className="nav-header">CONTEÚDO</li>
              <NavItem m="dashboard" icon="fas fa-tasks" label="Aprovação" badge={pendingCount} />
              <NavItem m="generate" icon="fas fa-magic" label="Gerar com IA" />

              <li className="nav-header">AGENTES IA</li>
              <NavItem m="agent" icon="fas fa-robot" label="Mara — Social" />
              <NavItem m="designer" icon="fas fa-palette" label="Pixel — Designer" />
              <NavItem m="ads" icon="fab fa-google" label="Luna — Google Ads" />

              <li className="nav-header">PLANEJAMENTO</li>
              <NavItem m="calendar" icon="fas fa-calendar-alt" label="Calendário" />
              <NavItem m="strategy" icon="fas fa-chess" label="Estratégia" />

              <li className="nav-header">GESTÃO</li>
              <NavItem m="businesses" icon="fas fa-building" label="Businesses" />
              <NavItem m="history" icon="fas fa-history" label="Histórico" />
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
