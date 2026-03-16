import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business, BrandStrategy, PostAnalytics } from '../services/api'

const TONE_OPTIONS = ['profissional', 'descontraido', 'urgente', 'educativo', 'inspiracional', 'humoristico']

export function StrategyPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [strategy, setStrategy] = useState<BrandStrategy>({})
  const [analytics, setAnalytics] = useState<PostAnalytics | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  // Form state
  const [pillarsInput, setPillarsInput] = useState('')
  const [goalsInput, setGoalsInput] = useState('')
  const [competitorsInput, setCompetitorsInput] = useState('')
  const [brandTone, setBrandTone] = useState('')
  const [postsPerWeek, setPostsPerWeek] = useState('5')

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) return
    setLoading(true)
    Promise.all([
      api.getStrategy(selectedBusiness),
      api.postAnalytics(selectedBusiness),
    ])
      .then(([strat, anal]) => {
        setStrategy(strat)
        setAnalytics(anal)
        setPillarsInput((strat.content_pillars || []).join(', '))
        setGoalsInput((strat.goals || []).join('\n'))
        setCompetitorsInput((strat.competitors || []).join(', '))
        setBrandTone(strat.brand_tone || '')
        setPostsPerWeek(String(strat.posting_frequency?.posts_per_week ?? 5))
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedBusiness])

  const handleSave = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.updateStrategy(selectedBusiness, {
        content_pillars: pillarsInput.split(',').map(s => s.trim()).filter(Boolean),
        brand_tone: brandTone || undefined,
        posting_frequency: { posts_per_week: Number(postsPerWeek) },
        goals: goalsInput.split('\n').map(s => s.trim()).filter(Boolean),
        competitors: competitorsInput.split(',').map(s => s.trim()).filter(Boolean),
      })
      setMsg('Estratégia salva com sucesso!')
    } catch (e: any) {
      setMsg(`Erro: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="row mb-3">
        <div className="col-md-4">
          <select
            className="form-control"
            value={selectedBusiness}
            onChange={e => setSelectedBusiness(e.target.value)}
          >
            <option value="">Selecione um business...</option>
            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      </div>

      {!selectedBusiness && (
        <div className="text-center text-muted mt-5">
          <i className="fas fa-chess fa-3x mb-3" style={{ opacity: 0.3 }} />
          <p>Selecione um business para configurar a estratégia de marca.</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-4">
          <div className="spinner-border text-primary" />
        </div>
      )}

      {selectedBusiness && !loading && (
        <div className="row">
          {/* Strategy Form */}
          <div className="col-md-7">
            <div className="card card-primary">
              <div className="card-header">
                <h3 className="card-title"><i className="fas fa-chess mr-2" /> Estratégia de Marca</h3>
              </div>
              <div className="card-body">
                {msg && (
                  <div className={`alert ${msg.startsWith('Erro') ? 'alert-danger' : 'alert-success'} alert-dismissible`}>
                    {msg}
                    <button type="button" className="close" onClick={() => setMsg('')}>&times;</button>
                  </div>
                )}

                <div className="form-group">
                  <label className="font-weight-bold">
                    <i className="fas fa-columns mr-1" /> Pilares de Conteúdo
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="educação, promoção, inspiração, bastidores..."
                    value={pillarsInput}
                    onChange={e => setPillarsInput(e.target.value)}
                  />
                  <small className="text-muted">Separe com vírgulas</small>
                </div>

                <div className="form-group">
                  <label className="font-weight-bold">
                    <i className="fas fa-microphone mr-1" /> Tom de Voz
                  </label>
                  <select
                    className="form-control"
                    value={brandTone}
                    onChange={e => setBrandTone(e.target.value)}
                  >
                    <option value="">Selecione...</option>
                    {TONE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>

                <div className="form-group">
                  <label className="font-weight-bold">
                    <i className="fas fa-calendar mr-1" /> Posts por Semana
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    min={1}
                    max={21}
                    value={postsPerWeek}
                    onChange={e => setPostsPerWeek(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="font-weight-bold">
                    <i className="fas fa-bullseye mr-1" /> Objetivos
                  </label>
                  <textarea
                    className="form-control"
                    rows={3}
                    placeholder="Um objetivo por linha..."
                    value={goalsInput}
                    onChange={e => setGoalsInput(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="font-weight-bold">
                    <i className="fas fa-binoculars mr-1" /> Concorrentes
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Concorrente A, Concorrente B..."
                    value={competitorsInput}
                    onChange={e => setCompetitorsInput(e.target.value)}
                  />
                  <small className="text-muted">Separe com vírgulas</small>
                </div>

                <button
                  className="btn btn-primary"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving
                    ? <><span className="spinner-border spinner-border-sm mr-1" /> Salvando...</>
                    : <><i className="fas fa-save mr-1" /> Salvar Estratégia</>
                  }
                </button>
              </div>
            </div>
          </div>

          {/* Analytics */}
          <div className="col-md-5">
            {analytics && (
              <>
                <div className="row">
                  <div className="col-6">
                    <div className="info-box bg-info">
                      <span className="info-box-icon"><i className="fas fa-file-alt" /></span>
                      <div className="info-box-content">
                        <span className="info-box-text">Total Rascunhos</span>
                        <span className="info-box-number">{analytics.total_drafts}</span>
                      </div>
                    </div>
                  </div>
                  <div className="col-6">
                    <div className="info-box bg-success">
                      <span className="info-box-icon"><i className="fas fa-check" /></span>
                      <div className="info-box-content">
                        <span className="info-box-text">Taxa Aprovação</span>
                        <span className="info-box-number">{analytics.approval_rate_pct}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="col-6">
                    <div className="info-box bg-warning">
                      <span className="info-box-icon"><i className="fas fa-share-square" /></span>
                      <div className="info-box-content">
                        <span className="info-box-text">Publicados</span>
                        <span className="info-box-number">{analytics.published}</span>
                      </div>
                    </div>
                  </div>
                  <div className="col-6">
                    <div className="info-box bg-danger">
                      <span className="info-box-icon"><i className="fas fa-times" /></span>
                      <div className="info-box-content">
                        <span className="info-box-text">Rejeitados</span>
                        <span className="info-box-number">{analytics.rejected}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {analytics.top_formats.length > 0 && (
                  <div className="card card-outline card-secondary">
                    <div className="card-header py-2">
                      <h6 className="card-title m-0">Formatos Mais Aprovados</h6>
                    </div>
                    <div className="card-body py-2">
                      {analytics.top_formats.map(f => (
                        <div key={f.format} className="d-flex justify-content-between mb-1">
                          <span className="text-capitalize">{f.format}</span>
                          <span className="badge badge-info">{f.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analytics.best_times.length > 0 && (
                  <div className="card card-outline card-secondary">
                    <div className="card-header py-2">
                      <h6 className="card-title m-0">Melhores Horários</h6>
                    </div>
                    <div className="card-body py-2">
                      {analytics.best_times.map(t => (
                        <div key={t.time} className="d-flex justify-content-between mb-1">
                          <span>{t.time}</span>
                          <span className="badge badge-success">{t.count}x</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
