import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business, ReadinessResponse } from '../services/api'

const NICHES = [
  'dentista', 'ecommerce', 'restaurante', 'academia', 'clinica',
  'automovel', 'imobiliaria', 'salao-beleza', 'advocacia', 'contabilidade',
  'educacao', 'tecnologia', 'moda', 'saude', 'alimentacao', 'outros',
]

export function BusinessPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [readiness, setReadiness] = useState<Record<string, ReadinessResponse>>({})
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', type: '' })
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    const list = await api.listBusinesses()
    setBusinesses(list)
    // Load readiness for each
    const readinessMap: Record<string, ReadinessResponse> = {}
    await Promise.all(list.map(async (b) => {
      try {
        readinessMap[b.id] = await api.getReadiness(b.id)
      } catch { /* ignore */ }
    }))
    setReadiness(readinessMap)
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.type) return
    setLoading(true)
    try {
      const result = await api.createBusiness({ name: form.name, type: form.type })
      setShowForm(false)
      setForm({ name: '', type: '' })
      // Navigate to onboarding for this business
      window.dispatchEvent(new CustomEvent('navigate', { detail: { module: 'onboarding', businessId: result.id } }))
    } catch (e: any) {
      setMsg(`Erro: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const goToOnboarding = (businessId: string) => {
    window.dispatchEvent(new CustomEvent('navigate', { detail: { module: 'onboarding', businessId } }))
  }

  const deleteBusiness = async (id: string, name: string) => {
    if (!confirm(`Excluir "${name}"? Esta ação não pode ser desfeita.`)) return
    try {
      await api.deleteBusiness(id)
      load()
    } catch (e: any) {
      setMsg('Erro: ' + e.message)
    }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="m-0">Seus negócios</h5>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <i className="fas fa-plus mr-2" />Novo negócio
        </button>
      </div>

      {msg && (
        <div className="alert alert-info alert-dismissible">
          {msg}
          <button className="close" onClick={() => setMsg('')}>&times;</button>
        </div>
      )}

      {showForm && (
        <div className="card mb-4" style={{ borderTop: '3px solid #6f42c1' }}>
          <div className="card-header"><h3 className="card-title">Novo negócio</h3></div>
          <form onSubmit={handleCreate}>
            <div className="card-body">
              <div className="row">
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Nome da empresa *</label>
                  <input className="form-control" required value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    placeholder="Ex: Clínica Sorriso Perfeito" />
                </div>
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Segmento *</label>
                  <select className="form-control" value={form.type} required
                    onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                    <option value="">Selecione...</option>
                    {NICHES.map(n => (
                      <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1).replace('-', ' ')}</option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-muted small mb-0">
                <i className="fas fa-info-circle mr-1" />
                Após criar, você será direcionado para configurar o perfil completo do negócio.
              </p>
            </div>
            <div className="card-footer">
              <button type="submit" className="btn btn-primary" disabled={loading || !form.name || !form.type}>
                {loading ? <span className="spinner-border spinner-border-sm mr-1" /> : <i className="fas fa-arrow-right mr-1" />}
                Criar e configurar
              </button>
              <button type="button" className="btn btn-default ml-2" onClick={() => setShowForm(false)}>Cancelar</button>
            </div>
          </form>
        </div>
      )}

      {businesses.length === 0 && !showForm && (
        <div className="card">
          <div className="card-body text-center py-5">
            <i className="fas fa-building fa-3x mb-3 d-block" style={{ opacity: 0.3 }} />
            <h5>Nenhum negócio cadastrado</h5>
            <p className="text-muted">Cadastre seu primeiro negócio para a agência IA começar a trabalhar.</p>
            <button className="btn btn-primary btn-lg" onClick={() => setShowForm(true)}>
              <i className="fas fa-plus mr-2" />Cadastrar meu negócio
            </button>
          </div>
        </div>
      )}

      <div className="row">
        {businesses.map(b => {
          const r = readiness[b.id]
          const scoreColor = r ? (r.score >= 60 ? 'success' : r.score >= 30 ? 'warning' : 'danger') : 'secondary'
          return (
            <div key={b.id} className="col-md-6 col-lg-4">
              <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h3 className="card-title mb-0">{b.name}</h3>
                  <span className="badge badge-secondary">{b.type}</span>
                </div>
                <div className="card-body">
                  {b.description && (
                    <p className="small text-muted mb-2" style={{ lineHeight: 1.4 }}>
                      {(b.description as string).slice(0, 120)}{(b.description as string).length > 120 ? '...' : ''}
                    </p>
                  )}

                  {r && (
                    <div className="mb-2">
                      <div className="d-flex justify-content-between mb-1">
                        <span className="small font-weight-bold">Perfil: {r.score}%</span>
                        <span className="small text-muted">{r.filled_fields}/{r.total_fields}</span>
                      </div>
                      <div className="progress" style={{ height: 6 }}>
                        <div className={`progress-bar bg-${scoreColor}`} style={{ width: `${r.score}%` }} />
                      </div>
                      {r.score < 60 && (
                        <small className="text-danger">
                          <i className="fas fa-exclamation-triangle mr-1" />
                          Complete o perfil para criar conteúdo de qualidade
                        </small>
                      )}
                    </div>
                  )}

                  <div className="d-flex flex-wrap" style={{ gap: 4, fontSize: 11 }}>
                    {b.website_url && <span className="badge badge-light"><i className="fas fa-globe mr-1" />Site</span>}
                    {b.instagram_handle && <span className="badge badge-light"><i className="fab fa-instagram mr-1" />{b.instagram_handle}</span>}
                    {b.instagram_account_id && <span className="badge badge-success"><i className="fab fa-instagram mr-1" />API conectada</span>}
                    {b.location && <span className="badge badge-light"><i className="fas fa-map-marker-alt mr-1" />{b.location}</span>}
                  </div>
                </div>
                <div className="card-footer d-flex justify-content-between">
                  <button className="btn btn-sm btn-primary" onClick={() => goToOnboarding(b.id)}>
                    <i className="fas fa-edit mr-1" />{r && r.score < 60 ? 'Completar perfil' : 'Editar perfil'}
                  </button>
                  <button className="btn btn-sm btn-outline-danger" onClick={() => deleteBusiness(b.id, b.name)}>
                    <i className="fas fa-trash" />
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
