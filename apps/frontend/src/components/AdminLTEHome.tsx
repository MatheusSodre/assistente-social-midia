import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'

interface Stats {
  pending: number
  approved: number
  published: number
  businesses: number
}

interface QuickActionProps {
  icon: string
  label: string
  description: string
  color: string
  onClick: () => void
}

function QuickAction({ icon, label, description, color, onClick }: QuickActionProps) {
  return (
    <div
      className="col-md-3 col-sm-6 mb-3"
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <div
        className={`info-box shadow-sm`}
        style={{ borderRadius: 12, transition: 'transform 0.15s, box-shadow 0.15s', overflow: 'hidden' }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)'
          ;(e.currentTarget as HTMLElement).style.boxShadow = '0 8px 20px rgba(0,0,0,0.12)'
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLElement).style.transform = ''
          ;(e.currentTarget as HTMLElement).style.boxShadow = ''
        }}
      >
        <span className={`info-box-icon bg-${color}`} style={{ borderRadius: 0 }}>
          <i className={`fas fa-${icon}`} />
        </span>
        <div className="info-box-content">
          <span className="info-box-text font-weight-bold">{label}</span>
          <span className="info-box-number" style={{ fontSize: 12, fontWeight: 400, color: '#666' }}>{description}</span>
        </div>
      </div>
    </div>
  )
}

interface AdminLTEHomeProps {
  onNavigate?: (module: string) => void
}

export function AdminLTEHome({ onNavigate }: AdminLTEHomeProps) {
  const { usuario } = useAuth()
  const [stats, setStats] = useState<Stats>({ pending: 0, approved: 0, published: 0, businesses: 0 })
  const [loading, setLoading] = useState(true)
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'

  useEffect(() => {
    async function load() {
      try {
        const [businesses, pending, all] = await Promise.all([
          api.listBusinesses(),
          api.listDrafts('pending_approval'),
          api.listDrafts(),
        ])
        const published = all.filter(d => d.status === 'published').length
        const approved = all.filter(d => d.status === 'approved').length
        setStats({ pending: pending.length, approved, published, businesses: businesses.length })
      } catch {
        // silently fail
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const firstName = usuario?.nome?.split(' ')[0] ?? 'usuário'

  return (
    <div>
      {/* Saudação */}
      <div className="row mb-2">
        <div className="col-12">
          <div
            className="card mb-0"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: 16,
              color: '#fff',
            }}
          >
            <div className="card-body py-4 px-4">
              <div className="d-flex align-items-center justify-content-between flex-wrap" style={{ gap: 16 }}>
                <div>
                  <h2 className="mb-1" style={{ fontWeight: 700, fontSize: 26 }}>
                    {greeting}, {firstName}! 👋
                  </h2>
                  <p className="mb-0" style={{ opacity: 0.85, fontSize: 15 }}>
                    {stats.pending > 0
                      ? `Você tem ${stats.pending} post${stats.pending > 1 ? 's' : ''} aguardando sua aprovação.`
                      : 'Tudo em dia! Que tal criar novo conteúdo?'}
                  </p>
                </div>
                <div className="d-flex" style={{ gap: 10 }}>
                  <button
                    className="btn btn-light btn-sm font-weight-bold"
                    style={{ borderRadius: 8, color: '#764ba2' }}
                    onClick={() => onNavigate?.('agency')}
                  >
                    <i className="fas fa-magic mr-1" /> Criar conteúdo
                  </button>
                  {stats.pending > 0 && (
                    <button
                      className="btn btn-warning btn-sm font-weight-bold"
                      style={{ borderRadius: 8 }}
                      onClick={() => onNavigate?.('dashboard')}
                    >
                      <i className="fas fa-tasks mr-1" /> Ver aprovações
                      <span className="badge badge-dark ml-1">{stats.pending}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Métricas */}
      <div className="row mt-3">
        {loading ? (
          <div className="col-12 text-center py-4">
            <span className="spinner-border spinner-border-sm text-primary" />
          </div>
        ) : (
          <>
            <div className="col-lg-3 col-6">
              <div className="small-box" style={{ borderRadius: 12, background: '#fff3cd', overflow: 'hidden' }}>
                <div className="inner">
                  <h3 style={{ color: '#856404' }}>{stats.pending}</h3>
                  <p style={{ color: '#856404' }}>Aguardando aprovação</p>
                </div>
                <div className="icon" style={{ color: 'rgba(133,100,4,0.15)' }}>
                  <i className="fas fa-clock" />
                </div>
                <a
                  href="#"
                  className="small-box-footer"
                  style={{ background: '#ffc107', color: '#fff', fontWeight: 600 }}
                  onClick={e => { e.preventDefault(); onNavigate?.('dashboard') }}
                >
                  Revisar <i className="fas fa-arrow-circle-right" />
                </a>
              </div>
            </div>

            <div className="col-lg-3 col-6">
              <div className="small-box" style={{ borderRadius: 12, background: '#d4edda', overflow: 'hidden' }}>
                <div className="inner">
                  <h3 style={{ color: '#155724' }}>{stats.approved}</h3>
                  <p style={{ color: '#155724' }}>Aprovados</p>
                </div>
                <div className="icon" style={{ color: 'rgba(21,87,36,0.15)' }}>
                  <i className="fas fa-check-circle" />
                </div>
                <a
                  href="#"
                  className="small-box-footer"
                  style={{ background: '#28a745', color: '#fff', fontWeight: 600 }}
                  onClick={e => { e.preventDefault(); onNavigate?.('calendar') }}
                >
                  Ver calendário <i className="fas fa-arrow-circle-right" />
                </a>
              </div>
            </div>

            <div className="col-lg-3 col-6">
              <div className="small-box" style={{ borderRadius: 12, background: '#cce5ff', overflow: 'hidden' }}>
                <div className="inner">
                  <h3 style={{ color: '#004085' }}>{stats.published}</h3>
                  <p style={{ color: '#004085' }}>Publicados</p>
                </div>
                <div className="icon" style={{ color: 'rgba(0,64,133,0.15)' }}>
                  <i className="fab fa-instagram" />
                </div>
                <a
                  href="#"
                  className="small-box-footer"
                  style={{ background: '#007bff', color: '#fff', fontWeight: 600 }}
                  onClick={e => { e.preventDefault(); onNavigate?.('history') }}
                >
                  Histórico <i className="fas fa-arrow-circle-right" />
                </a>
              </div>
            </div>

            <div className="col-lg-3 col-6">
              <div className="small-box" style={{ borderRadius: 12, background: '#e2d9f3', overflow: 'hidden' }}>
                <div className="inner">
                  <h3 style={{ color: '#432874' }}>{stats.businesses}</h3>
                  <p style={{ color: '#432874' }}>Businesses</p>
                </div>
                <div className="icon" style={{ color: 'rgba(67,40,116,0.15)' }}>
                  <i className="fas fa-building" />
                </div>
                <a
                  href="#"
                  className="small-box-footer"
                  style={{ background: '#6f42c1', color: '#fff', fontWeight: 600 }}
                  onClick={e => { e.preventDefault(); onNavigate?.('businesses') }}
                >
                  Gerenciar <i className="fas fa-arrow-circle-right" />
                </a>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Ações rápidas */}
      <div className="row mt-1">
        <div className="col-12">
          <h6 className="text-muted text-uppercase mb-3" style={{ fontSize: 11, letterSpacing: 1 }}>
            <i className="fas fa-bolt mr-1" /> Acesso rápido
          </h6>
        </div>
        <QuickAction icon="magic" label="Criar Conteúdo" description="Posts, stories e reels com IA" color="primary" onClick={() => onNavigate?.('agency')} />
        <QuickAction icon="check-double" label="Revisar & Aprovar" description="Conteúdo aguardando aprovação" color="warning" onClick={() => onNavigate?.('dashboard')} />
        <QuickAction icon="chess" label="Estratégia & Marca" description="Defina tom, cores e pilares" color="success" onClick={() => onNavigate?.('strategy')} />
        <QuickAction icon="calendar-alt" label="Calendário" description="Agende suas publicações" color="info" onClick={() => onNavigate?.('calendar')} />
      </div>
    </div>
  )
}
