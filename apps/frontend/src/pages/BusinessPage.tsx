import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business } from '../services/api'

const NICHES = ['dentista', 'ecommerce', 'restaurante', 'academia', 'clinica', 'automovel', 'imobiliaria', 'salao-beleza', 'outros']

export function BusinessPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', type: 'dentista' })
  const [igForm, setIgForm] = useState({ businessId: '', account_id: '', token: '' })
  const [showIgModal, setShowIgModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const load = () => api.listBusinesses().then(setBusinesses)
  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.createBusiness(form)
      setMsg('Business criado!')
      setShowForm(false)
      setForm({ name: '', type: 'dentista' })
      load()
    } catch (e: any) {
      setMsg(`Erro: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectIg = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.connectInstagram(igForm.businessId, {
        instagram_account_id: igForm.account_id,
        access_token: igForm.token,
      })
      setMsg('Instagram conectado com sucesso!')
      setShowIgModal(false)
      load()
    } catch (e: any) {
      setMsg(`Erro: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="m-0">Suas empresas cadastradas</h5>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <i className="fas fa-plus mr-2" />Novo Business
        </button>
      </div>

      {msg && (
        <div className="alert alert-info alert-dismissible">
          {msg}
          <button className="close" onClick={() => setMsg('')}>×</button>
        </div>
      )}

      {showForm && (
        <div className="card card-primary mb-4">
          <div className="card-header"><h3 className="card-title">Novo Business</h3></div>
          <form onSubmit={handleCreate}>
            <div className="card-body">
              <div className="form-group">
                <label>Nome da Empresa</label>
                <input className="form-control" required value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Ex: Clínica Sorriso Perfeito" />
              </div>
              <div className="form-group">
                <label>Nicho</label>
                <select className="form-control" value={form.type}
                  onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                  {NICHES.map(n => (
                    <option key={n} value={n}>
                      {n.charAt(0).toUpperCase() + n.slice(1).replace('-', ' ')}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="card-footer">
              <button type="submit" className="btn btn-primary" disabled={loading}>Criar</button>
              <button type="button" className="btn btn-default ml-2" onClick={() => setShowForm(false)}>Cancelar</button>
            </div>
          </form>
        </div>
      )}

      <div className="row">
        {businesses.length === 0 && (
          <div className="col-12">
            <div className="card">
              <div className="card-body text-center text-muted py-5">
                <i className="fas fa-building fa-3x mb-3 d-block" />
                <p>Nenhum business cadastrado. Clique em "Novo Business" para começar.</p>
              </div>
            </div>
          </div>
        )}
        {businesses.map(b => (
          <div key={b.id} className="col-md-6 col-lg-4">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{b.name}</h3>
                <div className="card-tools">
                  <span className="badge badge-secondary">{b.type}</span>
                </div>
              </div>
              <div className="card-body">
                {b.instagram_account_id ? (
                  <p className="text-success"><i className="fab fa-instagram mr-2" />Conectado: {b.instagram_account_id}</p>
                ) : (
                  <p className="text-muted"><i className="fab fa-instagram mr-2" />Instagram não conectado</p>
                )}
              </div>
              <div className="card-footer">
                <button
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => {
                    setIgForm({ businessId: b.id, account_id: '', token: '' })
                    setShowIgModal(true)
                  }}
                >
                  <i className="fab fa-instagram mr-1" />
                  {b.instagram_account_id ? 'Reconectar' : 'Conectar'} Instagram
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showIgModal && (
        <div className="modal show d-block" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Conectar Instagram</h5>
                <button className="close" onClick={() => setShowIgModal(false)}>×</button>
              </div>
              <form onSubmit={handleConnectIg}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Instagram Account ID</label>
                    <input className="form-control" required value={igForm.account_id}
                      onChange={e => setIgForm(f => ({ ...f, account_id: e.target.value }))}
                      placeholder="Ex: 17841400000000000" />
                    <small className="text-muted">ID da conta do Instagram Business na Meta Graph API</small>
                  </div>
                  <div className="form-group">
                    <label>Access Token</label>
                    <input className="form-control" required type="password" value={igForm.token}
                      onChange={e => setIgForm(f => ({ ...f, token: e.target.value }))}
                      placeholder="Token da Meta Graph API" />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="submit" className="btn btn-primary" disabled={loading}>Conectar</button>
                  <button type="button" className="btn btn-default" onClick={() => setShowIgModal(false)}>Cancelar</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
