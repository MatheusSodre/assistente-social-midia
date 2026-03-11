import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type { Module } from './AdminLTEApp'
import { AdminLTEHome } from './AdminLTEHome'

export function AdminLTELayout() {
  const { usuario, logout } = useAuth()
  const [modulo, setModulo] = useState<Module>('home')

  useEffect(() => {
    const prev = document.body.className
    document.body.className = 'hold-transition sidebar-mini layout-fixed'
    return () => { document.body.className = prev }
  }, [])

  function renderModulo() {
    switch (modulo) {
      case 'home':
        return <AdminLTEHome />
      // Adicionar novos módulos aqui
      default:
        return <AdminLTEHome />
    }
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
        </ul>
        <ul className="navbar-nav ml-auto">
          <li className="nav-item dropdown">
            <a className="nav-link" data-toggle="dropdown" href="#">
              <i className="far fa-user" /> {usuario?.nome}
            </a>
            <div className="dropdown-menu dropdown-menu-right">
              <button className="dropdown-item" onClick={logout}>
                <i className="fas fa-sign-out-alt mr-2" />
                Sair
              </button>
            </div>
          </li>
        </ul>
      </nav>

      {/* Sidebar */}
      <aside className="main-sidebar sidebar-dark-primary elevation-4">
        <a href="#" className="brand-link">
          <span className="brand-text font-weight-light">Meu Projeto</span>
        </a>
        <div className="sidebar">
          <nav className="mt-2">
            <ul
              className="nav nav-pills nav-sidebar flex-column"
              data-widget="treeview"
              role="menu"
            >
              <li className="nav-item">
                <a
                  href="#"
                  className={`nav-link ${modulo === 'home' ? 'active' : ''}`}
                  onClick={(e) => { e.preventDefault(); setModulo('home') }}
                >
                  <i className="nav-icon fas fa-home" />
                  <p>Início</p>
                </a>
              </li>
              {/* Adicionar novos itens de menu aqui */}
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
                <h1 className="m-0">{modulo.charAt(0).toUpperCase() + modulo.slice(1)}</h1>
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

      {/* Footer */}
      <footer className="main-footer">
        <strong>Meu Projeto</strong> — Todos os direitos reservados.
      </footer>
    </div>
  )
}
