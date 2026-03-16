import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business, ContentDraft } from '../services/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const FORMATS: { value: string; label: string; icon: string; desc: string }[] = [
  { value: 'post', label: 'Post', icon: 'fa-th', desc: '1:1 Feed' },
  { value: 'story', label: 'Story', icon: 'fa-image', desc: '9:16 Stories' },
  { value: 'reel', label: 'Reel', icon: 'fa-film', desc: 'Vídeo curto' },
]

const TONES: { value: string; label: string; emoji: string }[] = [
  { value: 'profissional', label: 'Profissional', emoji: '💼' },
  { value: 'descontraido', label: 'Descontraído', emoji: '😄' },
  { value: 'urgente', label: 'Urgente', emoji: '🔥' },
  { value: 'educativo', label: 'Educativo', emoji: '📚' },
]

type Step = 'form' | 'loading' | 'result'

export function GeneratePage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [form, setForm] = useState({
    business_id: '',
    objective: '',
    format: 'post' as 'post' | 'story' | 'reel',
    tone: 'profissional' as 'profissional' | 'descontraido' | 'urgente' | 'educativo',
    audience: '',
  })
  const [step, setStep] = useState<Step>('form')
  const [imageLoading, setImageLoading] = useState(false)
  const [result, setResult] = useState<ContentDraft | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listBusinesses().then(b => {
      setBusinesses(b)
      if (b.length > 0) setForm(f => ({ ...f, business_id: b[0].id }))
    })
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.business_id) { setError('Selecione um business'); return }
    if (!form.objective.trim()) { setError('Descreva o objetivo do post'); return }
    setStep('loading')
    setError('')
    setResult(null)
    try {
      const draft = await api.generateContent(form)
      setResult(draft)
      setStep('result')
    } catch (e: any) {
      setError(e.message)
      setStep('form')
    }
  }

  const handleRegenImage = async () => {
    if (!result) return
    setImageLoading(true)
    try {
      const res = await api.generateImage(result.id)
      setResult(r => r ? { ...r, image_url: res.image_url } : r)
    } catch (e: any) {
      setError(`Erro ao gerar imagem: ${e.message}`)
    } finally {
      setImageLoading(false)
    }
  }

  const imgSrc = (url?: string) => url?.startsWith('/') ? `${API_BASE}${url}` : url ?? ''

  // ── Segmented control reutilizável
  function ToggleGroup<T extends string>({
    options, value, onChange,
  }: {
    options: { value: T; label: string; icon?: string; emoji?: string; desc?: string }[]
    value: T
    onChange: (v: T) => void
  }) {
    return (
      <div className="d-flex flex-wrap" style={{ gap: 8 }}>
        {options.map(opt => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            style={{
              flex: 1, minWidth: 80,
              padding: '8px 12px',
              borderRadius: 10,
              border: `2px solid ${value === opt.value ? '#007bff' : '#dee2e6'}`,
              background: value === opt.value ? '#e8f0fe' : '#fff',
              color: value === opt.value ? '#0056b3' : '#555',
              fontWeight: value === opt.value ? 700 : 400,
              fontSize: 13,
              cursor: 'pointer',
              transition: 'all 0.15s',
              textAlign: 'center',
            }}
          >
            {opt.icon && <i className={`fas ${opt.icon} d-block mb-1`} style={{ fontSize: 16 }} />}
            {opt.emoji && <span style={{ fontSize: 18, display: 'block', marginBottom: 2 }}>{opt.emoji}</span>}
            <div>{opt.label}</div>
            {opt.desc && <div style={{ fontSize: 10, opacity: 0.6, fontWeight: 400 }}>{opt.desc}</div>}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="row">
      {/* Formulário */}
      <div className={`col-md-${step === 'result' ? '4' : '7'} mx-auto`} style={{ transition: 'all 0.3s' }}>
        <div className="card card-primary">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fas fa-magic mr-2" />Configurar conteúdo
            </h3>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="card-body">
              {error && (
                <div className="alert alert-danger d-flex align-items-center" style={{ gap: 8, borderRadius: 8 }}>
                  <i className="fas fa-exclamation-circle" />
                  {error}
                </div>
              )}

              {/* Business */}
              {businesses.length === 0 ? (
                <div className="alert alert-warning" style={{ borderRadius: 8 }}>
                  <i className="fas fa-building mr-2" />
                  Crie um business primeiro na aba <strong>Businesses</strong>.
                </div>
              ) : (
                <div className="form-group">
                  <label className="small font-weight-bold text-muted text-uppercase" style={{ letterSpacing: 0.5 }}>
                    Empresa
                  </label>
                  <select
                    className="form-control"
                    value={form.business_id}
                    onChange={e => setForm(f => ({ ...f, business_id: e.target.value }))}
                    style={{ borderRadius: 8 }}
                  >
                    {businesses.map(b => (
                      <option key={b.id} value={b.id}>{b.name} · {b.type}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Formato */}
              <div className="form-group">
                <label className="small font-weight-bold text-muted text-uppercase" style={{ letterSpacing: 0.5 }}>
                  Formato
                </label>
                <ToggleGroup
                  options={FORMATS}
                  value={form.format}
                  onChange={v => setForm(f => ({ ...f, format: v as typeof form.format }))}
                />
              </div>

              {/* Objetivo */}
              <div className="form-group">
                <label className="small font-weight-bold text-muted text-uppercase" style={{ letterSpacing: 0.5 }}>
                  Objetivo
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={form.objective}
                  onChange={e => setForm(f => ({ ...f, objective: e.target.value }))}
                  placeholder="Ex: Promoção de limpeza dental com 20% de desconto para novos pacientes"
                  style={{ borderRadius: 8, resize: 'none' }}
                />
              </div>

              {/* Tom de voz */}
              <div className="form-group">
                <label className="small font-weight-bold text-muted text-uppercase" style={{ letterSpacing: 0.5 }}>
                  Tom de voz
                </label>
                <ToggleGroup
                  options={TONES}
                  value={form.tone}
                  onChange={v => setForm(f => ({ ...f, tone: v as typeof form.tone }))}
                />
              </div>

              {/* Público */}
              <div className="form-group mb-0">
                <label className="small font-weight-bold text-muted text-uppercase" style={{ letterSpacing: 0.5 }}>
                  Público-alvo <span className="text-muted font-weight-normal">(opcional)</span>
                </label>
                <input
                  className="form-control"
                  value={form.audience}
                  onChange={e => setForm(f => ({ ...f, audience: e.target.value }))}
                  placeholder="Ex: adultos 25–45, classe média, São Paulo"
                  style={{ borderRadius: 8 }}
                />
              </div>
            </div>

            <div className="card-footer">
              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={step === 'loading' || businesses.length === 0}
                style={{ borderRadius: 8, fontWeight: 600, padding: '10px' }}
              >
                {step === 'loading'
                  ? <><i className="fas fa-spinner fa-spin mr-2" />Gerando com IA...</>
                  : <><i className="fas fa-magic mr-2" />Gerar conteúdo</>}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Loading state */}
      {step === 'loading' && (
        <div className="col-md-8">
          <div className="card" style={{ borderRadius: 12 }}>
            <div className="card-body text-center py-5">
              <div style={{ fontSize: 48, marginBottom: 16 }}>✨</div>
              <h5 className="font-weight-bold">Criando seu conteúdo...</h5>
              <p className="text-muted small mb-4">A IA está escrevendo a caption, gerando hashtags e criando a imagem</p>
              <div className="d-flex justify-content-center" style={{ gap: 8 }}>
                {['Escrevendo caption', 'Gerando hashtags', 'Criando imagem'].map((label, i) => (
                  <div key={label} className="d-flex align-items-center text-muted small" style={{ gap: 6 }}>
                    <span
                      className="spinner-grow spinner-grow-sm"
                      style={{ animationDelay: `${i * 0.2}s` }}
                    />
                    {label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resultado */}
      {step === 'result' && result && (
        <div className="col-md-8">
          <div className="card" style={{ borderRadius: 12, overflow: 'hidden' }}>
            {/* Header */}
            <div
              className="card-header d-flex align-items-center justify-content-between"
              style={{ background: 'linear-gradient(135deg,#28a745,#20c997)', border: 'none' }}
            >
              <h3 className="card-title text-white mb-0">
                <i className="fas fa-check-circle mr-2" />Conteúdo gerado!
              </h3>
              <button
                className="btn btn-sm btn-outline-light"
                onClick={() => setStep('form')}
                style={{ borderRadius: 8 }}
              >
                <i className="fas fa-redo mr-1" />Novo
              </button>
            </div>

            <div className="card-body p-0">
              <div className="row no-gutters">
                {/* Imagem */}
                <div className="col-md-5 bg-dark d-flex align-items-center justify-content-center" style={{ minHeight: 300 }}>
                  {result.image_url ? (
                    <div style={{ width: '100%', position: 'relative' }}>
                      <img
                        src={imgSrc(result.image_url)}
                        alt="Gerada"
                        style={{ width: '100%', display: 'block', objectFit: 'cover', maxHeight: 400 }}
                      />
                      <button
                        className="btn btn-sm btn-dark"
                        onClick={handleRegenImage}
                        disabled={imageLoading}
                        style={{
                          position: 'absolute', bottom: 8, right: 8,
                          borderRadius: 8, opacity: 0.85,
                        }}
                      >
                        {imageLoading
                          ? <i className="fas fa-spinner fa-spin" />
                          : <><i className="fas fa-sync mr-1" />Regenerar</>}
                      </button>
                    </div>
                  ) : (
                    <div className="text-center p-4">
                      <i className="fas fa-image fa-3x text-secondary mb-3 d-block" />
                      <button
                        className="btn btn-warning btn-sm"
                        onClick={handleRegenImage}
                        disabled={imageLoading}
                        style={{ borderRadius: 8 }}
                      >
                        {imageLoading
                          ? <><i className="fas fa-spinner fa-spin mr-1" />Gerando...</>
                          : <><i className="fas fa-image mr-1" />Gerar imagem</>}
                      </button>
                    </div>
                  )}
                </div>

                {/* Texto */}
                <div className="col-md-7 p-4" style={{ maxHeight: 420, overflowY: 'auto' }}>
                  <div className="mb-3">
                    <div className="small font-weight-bold text-muted text-uppercase mb-1" style={{ letterSpacing: 0.5 }}>
                      Caption
                    </div>
                    <div
                      className="p-3 rounded"
                      style={{ background: '#f8f9fa', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}
                    >
                      {result.caption}
                    </div>
                  </div>

                  {result.hashtags?.length > 0 && (
                    <div className="mb-3">
                      <div className="small font-weight-bold text-muted text-uppercase mb-1" style={{ letterSpacing: 0.5 }}>
                        Hashtags
                      </div>
                      <div className="d-flex flex-wrap" style={{ gap: 4 }}>
                        {result.hashtags.map(h => (
                          <span key={h} className="badge badge-light border" style={{ fontSize: 11 }}>#{h}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.call_to_action && (
                    <div className="mb-3">
                      <div className="small font-weight-bold text-muted text-uppercase mb-1" style={{ letterSpacing: 0.5 }}>
                        Call to Action
                      </div>
                      <div style={{ fontSize: 13 }}>{result.call_to_action}</div>
                    </div>
                  )}

                  {result.best_posting_time && (
                    <div className="d-inline-flex align-items-center px-2 py-1 rounded" style={{ background: '#e8f5e9', gap: 6 }}>
                      <i className="fas fa-clock text-success" style={{ fontSize: 12 }} />
                      <span style={{ fontSize: 12, color: '#2e7d32' }}>
                        Melhor horário: <strong>{result.best_posting_time}</strong>
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div
              className="card-footer d-flex align-items-center justify-content-between"
              style={{ background: '#f8f9fa', borderTop: '1px solid #e9ecef' }}
            >
              <span className="small text-muted">
                <i className="fas fa-clock mr-1" />Aguardando aprovação
              </span>
              <a
                href="#"
                className="btn btn-sm btn-success"
                style={{ borderRadius: 8 }}
                onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent('navigate', { detail: 'dashboard' })) }}
              >
                <i className="fas fa-tasks mr-1" />Ir para Aprovação
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
