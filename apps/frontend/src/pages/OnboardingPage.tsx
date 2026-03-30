import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business, ReadinessResponse, BrandStrategy } from '../services/api'

interface OnboardingProps {
  businessId: string
  onComplete: () => void
}

const NICHES = [
  'dentista', 'ecommerce', 'restaurante', 'academia', 'clinica',
  'automovel', 'imobiliaria', 'salao-beleza', 'advocacia', 'contabilidade',
  'educacao', 'tecnologia', 'moda', 'saude', 'alimentacao', 'outros',
]

const TONES = [
  { value: 'profissional', label: 'Profissional' },
  { value: 'descontraido', label: 'Descontraído' },
  { value: 'educativo', label: 'Educativo' },
  { value: 'inspiracional', label: 'Inspiracional' },
  { value: 'humoristico', label: 'Humorístico' },
  { value: 'urgente', label: 'Urgente' },
]

export function OnboardingPage({ businessId, onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null)

  // Step 1 — Basics
  const [name, setName] = useState('')
  const [type, setType] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [instagramHandle, setInstagramHandle] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [servicesText, setServicesText] = useState('')
  const [targetAudience, setTargetAudience] = useState('')
  const [differentials, setDifferentials] = useState('')

  // Step 2 — Strategy
  const [brandTone, setBrandTone] = useState('')
  const [pillarsText, setPillarsText] = useState('')
  const [goalsText, setGoalsText] = useState('')
  const [competitorsText, setCompetitorsText] = useState('')

  // Step 3 — Visual
  const [primaryColor, setPrimaryColor] = useState('#000000')
  const [secondaryColor, setSecondaryColor] = useState('#FFFFFF')
  const [accentColor, setAccentColor] = useState('#FF6B35')
  const [styleDescription, setStyleDescription] = useState('')

  useEffect(() => {
    loadBusiness()
  }, [businessId])

  async function loadBusiness() {
    setLoading(true)
    try {
      const [biz, readinessData] = await Promise.all([
        api.getBusiness(businessId),
        api.getReadiness(businessId),
      ])
      setName(biz.name || '')
      setType(biz.type || '')
      setDescription(biz.description || '')
      setLocation(biz.location || '')
      setWebsiteUrl(biz.website_url || '')
      setInstagramHandle(biz.instagram_handle || '')
      setLinkedinUrl(biz.linkedin_url || '')
      setTargetAudience(biz.target_audience || '')
      setDifferentials(biz.differentials || '')
      const svc = biz.services
      if (Array.isArray(svc)) setServicesText(svc.join(', '))
      else if (typeof svc === 'string') {
        try { setServicesText(JSON.parse(svc).join(', ')) } catch { setServicesText(svc) }
      }
      setReadiness(readinessData)

      // Load strategy
      try {
        const strategy = await api.getStrategy(businessId)
        if (strategy.brand_tone) setBrandTone(strategy.brand_tone)
        if (strategy.content_pillars) setPillarsText(strategy.content_pillars.join(', '))
        if (strategy.goals) setGoalsText(strategy.goals.join('\n'))
        if (strategy.competitors) setCompetitorsText(strategy.competitors.join(', '))
      } catch { /* no strategy yet */ }

      // Load visual identity
      try {
        const vi = await api.getVisualIdentity(businessId)
        if (vi.primary_color) setPrimaryColor(vi.primary_color)
        if (vi.secondary_color) setSecondaryColor(vi.secondary_color)
        if (vi.accent_color) setAccentColor(vi.accent_color)
        if (vi.style_description) setStyleDescription(vi.style_description)
      } catch { /* no identity yet */ }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function saveStep1() {
    setSaving(true)
    try {
      const services = servicesText.split(',').map(s => s.trim()).filter(Boolean)
      await api.updateBusiness(businessId, {
        name, type, description, location,
        website_url: websiteUrl || undefined,
        instagram_handle: instagramHandle || undefined,
        linkedin_url: linkedinUrl || undefined,
        services: services.length > 0 ? services : undefined,
        target_audience: targetAudience || undefined,
        differentials: differentials || undefined,
      })
      const r = await api.getReadiness(businessId)
      setReadiness(r)
      setStep(2)
    } catch (e: any) {
      alert('Erro: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  async function saveStep2() {
    setSaving(true)
    try {
      const pillars = pillarsText.split(',').map(s => s.trim()).filter(Boolean)
      const goals = goalsText.split('\n').map(s => s.trim()).filter(Boolean)
      const competitors = competitorsText.split(',').map(s => s.trim()).filter(Boolean)
      await api.updateStrategy(businessId, {
        brand_tone: brandTone || undefined,
        content_pillars: pillars.length > 0 ? pillars : undefined,
        goals: goals.length > 0 ? goals : undefined,
        competitors: competitors.length > 0 ? competitors : undefined,
      })
      const r = await api.getReadiness(businessId)
      setReadiness(r)
      setStep(3)
    } catch (e: any) {
      alert('Erro: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  async function saveStep3() {
    setSaving(true)
    try {
      await api.updateVisualIdentity(businessId, {
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        accent_color: accentColor,
        style_description: styleDescription || undefined,
      })
      const r = await api.getReadiness(businessId)
      setReadiness(r)
      setStep(4)
    } catch (e: any) {
      alert('Erro: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  async function analyzeUrl() {
    const url = websiteUrl || instagramHandle
    if (!url) return
    setAnalyzing(true)
    setAnalysisResult(null)
    try {
      const urlToAnalyze = url.startsWith('http') || url.startsWith('@')
        ? url.replace(/^@/, 'https://instagram.com/')
        : url
      const res = await api.analyzeUrl(businessId, urlToAnalyze)
      setReadiness(res.readiness)

      // Auto-fill from extracted data
      const ext = res.extracted as Record<string, any>
      if (ext.description && !description) setDescription(ext.description)
      if (ext.services && !servicesText) {
        const svc = Array.isArray(ext.services) ? ext.services.join(', ') : ext.services
        setServicesText(svc)
      }
      if (ext.target_audience && !targetAudience) setTargetAudience(ext.target_audience)
      if (ext.differentials && !differentials) setDifferentials(ext.differentials)
      if (ext.location && !location) setLocation(ext.location)
      if (ext.brand_tone && !brandTone) setBrandTone(ext.brand_tone)
      if (ext.content_pillars && !pillarsText) {
        setPillarsText(Array.isArray(ext.content_pillars) ? ext.content_pillars.join(', ') : ext.content_pillars)
      }
      if (ext.goals && !goalsText) {
        setGoalsText(Array.isArray(ext.goals) ? ext.goals.join('\n') : ext.goals)
      }

      setAnalysisResult('Dados extraídos com sucesso! Revise os campos preenchidos.')
    } catch (e: any) {
      setAnalysisResult('Erro: ' + e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setAnalyzing(true)
    setAnalysisResult(null)
    try {
      const res = await api.uploadDocument(businessId, file)
      setReadiness(res.readiness)
      const ext = res.extracted as Record<string, any>
      if (ext.description && !description) setDescription(ext.description)
      if (ext.services && !servicesText) {
        setServicesText(Array.isArray(ext.services) ? ext.services.join(', ') : ext.services)
      }
      if (ext.target_audience && !targetAudience) setTargetAudience(ext.target_audience)
      if (ext.differentials && !differentials) setDifferentials(ext.differentials)
      setAnalysisResult(`Documento "${file.name}" analisado! Revise os campos.`)
    } catch (e: any) {
      setAnalysisResult('Erro: ' + e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) return (
    <div className="text-center py-5">
      <div className="spinner-border text-primary" />
      <p className="mt-2 text-muted">Carregando perfil...</p>
    </div>
  )

  const scoreColor = readiness ? (readiness.score >= 60 ? 'success' : readiness.score >= 30 ? 'warning' : 'danger') : 'secondary'

  return (
    <div className="row justify-content-center">
      <div className="col-lg-10">
        {/* Progress bar */}
        <div className="card mb-3">
          <div className="card-body py-3">
            <div className="d-flex align-items-center justify-content-between mb-2">
              <div className="d-flex align-items-center" style={{ gap: 16 }}>
                {[1, 2, 3, 4].map(s => (
                  <div
                    key={s}
                    className="d-flex align-items-center"
                    style={{ cursor: s < step ? 'pointer' : 'default' }}
                    onClick={() => s < step && setStep(s)}
                  >
                    <div
                      className="rounded-circle d-flex align-items-center justify-content-center"
                      style={{
                        width: 32, height: 32, fontSize: 13, fontWeight: 700,
                        background: s <= step ? '#6f42c1' : '#e9ecef',
                        color: s <= step ? '#fff' : '#adb5bd',
                      }}
                    >
                      {s < step ? <i className="fas fa-check" /> : s}
                    </div>
                    <span className="ml-2 d-none d-md-inline" style={{ fontSize: 13, color: s <= step ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      {s === 1 ? 'Negócio' : s === 2 ? 'Estratégia' : s === 3 ? 'Visual' : 'Pronto!'}
                    </span>
                    {s < 4 && <i className="fas fa-chevron-right mx-2 text-muted" style={{ fontSize: 10 }} />}
                  </div>
                ))}
              </div>
              {readiness && (
                <div className="text-right">
                  <span className={`badge badge-${scoreColor} px-3 py-2`} style={{ fontSize: 14 }}>
                    {readiness.score}% completo
                  </span>
                </div>
              )}
            </div>
            <div className="progress" style={{ height: 4 }}>
              <div className={`progress-bar bg-${scoreColor}`} style={{ width: `${readiness?.score ?? 0}%` }} />
            </div>
          </div>
        </div>

        {/* Step 1 — Negócio */}
        {step === 1 && (
          <div className="card">
            <div className="card-header" style={{ borderTop: '3px solid #6f42c1' }}>
              <h3 className="card-title"><i className="fas fa-building mr-2" />Sobre seu negócio</h3>
            </div>
            <div className="card-body">
              {/* AI Analysis box */}
              <div className="callout callout-info">
                <h5><i className="fas fa-robot mr-1" /> Análise automática</h5>
                <p className="mb-2 small">Cole o link do seu site, Instagram ou LinkedIn e a IA preenche automaticamente.</p>
                <div className="row">
                  <div className="col-md-5">
                    <input className="form-control form-control-sm" placeholder="https://seusite.com.br ou @instagram"
                      value={websiteUrl} onChange={e => setWebsiteUrl(e.target.value)} />
                  </div>
                  <div className="col-md-3">
                    <button className="btn btn-info btn-sm btn-block" onClick={analyzeUrl}
                      disabled={analyzing || (!websiteUrl && !instagramHandle)}>
                      {analyzing ? <><span className="spinner-border spinner-border-sm mr-1" />Analisando...</> : <><i className="fas fa-search mr-1" />Analisar</>}
                    </button>
                  </div>
                  <div className="col-md-4">
                    <label className="btn btn-outline-secondary btn-sm btn-block mb-0">
                      <i className="fas fa-file-pdf mr-1" />{analyzing ? 'Processando...' : 'Enviar PDF / documento'}
                      <input type="file" accept=".pdf,.doc,.docx,.txt" hidden onChange={handleFileUpload} disabled={analyzing} />
                    </label>
                  </div>
                </div>
                {analysisResult && (
                  <div className={`alert ${analysisResult.startsWith('Erro') ? 'alert-danger' : 'alert-success'} mt-2 mb-0 py-2 small`}>
                    {analysisResult}
                  </div>
                )}
              </div>

              <div className="row mt-3">
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Nome do negócio *</label>
                  <input className="form-control" value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Clínica Sorrir" />
                </div>
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Nicho / Segmento *</label>
                  <select className="form-control" value={type} onChange={e => setType(e.target.value)}>
                    <option value="">Selecione...</option>
                    {NICHES.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="font-weight-bold">Descrição do negócio</label>
                <textarea className="form-control" rows={3} value={description} onChange={e => setDescription(e.target.value)}
                  placeholder="O que sua empresa faz? Qual a proposta de valor? Conte em 2-3 frases..." />
                <small className="text-muted">Quanto mais detalhes, melhor a IA entende seu negócio.</small>
              </div>

              <div className="row">
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Produtos / Serviços</label>
                  <textarea className="form-control" rows={2} value={servicesText} onChange={e => setServicesText(e.target.value)}
                    placeholder="Limpeza dental, Clareamento, Implante, Ortodontia..." />
                  <small className="text-muted">Separados por vírgula</small>
                </div>
                <div className="col-md-6 form-group">
                  <label className="font-weight-bold">Público-alvo</label>
                  <textarea className="form-control" rows={2} value={targetAudience} onChange={e => setTargetAudience(e.target.value)}
                    placeholder="Mulheres 25-45 anos, classe B/C, interessadas em estética..." />
                </div>
              </div>

              <div className="form-group">
                <label className="font-weight-bold">Diferenciais</label>
                <textarea className="form-control" rows={2} value={differentials} onChange={e => setDifferentials(e.target.value)}
                  placeholder="O que diferencia seu negócio da concorrência?" />
              </div>

              <div className="row">
                <div className="col-md-4 form-group">
                  <label>Localização</label>
                  <input className="form-control" value={location} onChange={e => setLocation(e.target.value)} placeholder="São Paulo, SP" />
                </div>
                <div className="col-md-4 form-group">
                  <label>Instagram</label>
                  <input className="form-control" value={instagramHandle} onChange={e => setInstagramHandle(e.target.value)} placeholder="@seuinsta" />
                </div>
                <div className="col-md-4 form-group">
                  <label>LinkedIn</label>
                  <input className="form-control" value={linkedinUrl} onChange={e => setLinkedinUrl(e.target.value)} placeholder="linkedin.com/company/..." />
                </div>
              </div>
            </div>
            <div className="card-footer text-right">
              <button className="btn btn-primary" onClick={saveStep1} disabled={saving || !name || !type}>
                {saving ? <span className="spinner-border spinner-border-sm mr-1" /> : null}
                Próximo: Estratégia <i className="fas fa-arrow-right ml-1" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Estratégia */}
        {step === 2 && (
          <div className="card">
            <div className="card-header" style={{ borderTop: '3px solid #6f42c1' }}>
              <h3 className="card-title"><i className="fas fa-chess mr-2" />Estratégia de marca</h3>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="font-weight-bold">Tom de voz da marca</label>
                <select className="form-control" value={brandTone} onChange={e => setBrandTone(e.target.value)}>
                  <option value="">Selecione...</option>
                  {TONES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <small className="text-muted">Como sua marca se comunica com o público.</small>
              </div>

              <div className="form-group">
                <label className="font-weight-bold">Pilares de conteúdo</label>
                <input className="form-control" value={pillarsText} onChange={e => setPillarsText(e.target.value)}
                  placeholder="Educativo, Bastidores, Promoções, Depoimentos, Dicas..." />
                <small className="text-muted">Temas principais que sua marca aborda. Separados por vírgula.</small>
              </div>

              <div className="form-group">
                <label className="font-weight-bold">Objetivos</label>
                <textarea className="form-control" rows={3} value={goalsText} onChange={e => setGoalsText(e.target.value)}
                  placeholder={"Aumentar engajamento no Instagram\nAtrair novos clientes\nFortalecer a marca..."} />
                <small className="text-muted">Um objetivo por linha.</small>
              </div>

              <div className="form-group">
                <label>Concorrentes</label>
                <input className="form-control" value={competitorsText} onChange={e => setCompetitorsText(e.target.value)}
                  placeholder="Concorrente A, Concorrente B..." />
                <small className="text-muted">Separados por vírgula (opcional).</small>
              </div>
            </div>
            <div className="card-footer d-flex justify-content-between">
              <button className="btn btn-outline-secondary" onClick={() => setStep(1)}>
                <i className="fas fa-arrow-left mr-1" /> Voltar
              </button>
              <div>
                <button className="btn btn-outline-secondary mr-2" onClick={() => setStep(3)}>Pular</button>
                <button className="btn btn-primary" onClick={saveStep2} disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm mr-1" /> : null}
                  Próximo: Visual <i className="fas fa-arrow-right ml-1" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3 — Visual */}
        {step === 3 && (
          <div className="card">
            <div className="card-header" style={{ borderTop: '3px solid #6f42c1' }}>
              <h3 className="card-title"><i className="fas fa-palette mr-2" />Identidade visual</h3>
            </div>
            <div className="card-body">
              <p className="text-muted small mb-3">Defina as cores e estilo visual da sua marca. Isso ajuda a IA a criar conteúdo visualmente alinhado.</p>

              <div className="row">
                <div className="col-md-4 form-group">
                  <label className="font-weight-bold">Cor primária</label>
                  <div className="d-flex align-items-center" style={{ gap: 8 }}>
                    <input type="color" value={primaryColor} onChange={e => setPrimaryColor(e.target.value)} style={{ width: 40, height: 40, border: 'none', padding: 0 }} />
                    <input className="form-control form-control-sm" value={primaryColor} onChange={e => setPrimaryColor(e.target.value)} style={{ width: 100 }} />
                  </div>
                </div>
                <div className="col-md-4 form-group">
                  <label className="font-weight-bold">Cor secundária</label>
                  <div className="d-flex align-items-center" style={{ gap: 8 }}>
                    <input type="color" value={secondaryColor} onChange={e => setSecondaryColor(e.target.value)} style={{ width: 40, height: 40, border: 'none', padding: 0 }} />
                    <input className="form-control form-control-sm" value={secondaryColor} onChange={e => setSecondaryColor(e.target.value)} style={{ width: 100 }} />
                  </div>
                </div>
                <div className="col-md-4 form-group">
                  <label className="font-weight-bold">Cor de acento</label>
                  <div className="d-flex align-items-center" style={{ gap: 8 }}>
                    <input type="color" value={accentColor} onChange={e => setAccentColor(e.target.value)} style={{ width: 40, height: 40, border: 'none', padding: 0 }} />
                    <input className="form-control form-control-sm" value={accentColor} onChange={e => setAccentColor(e.target.value)} style={{ width: 100 }} />
                  </div>
                </div>
              </div>

              {/* Preview */}
              <div className="d-flex mb-3" style={{ gap: 8 }}>
                <div style={{ width: 80, height: 40, borderRadius: 6, background: primaryColor }} />
                <div style={{ width: 80, height: 40, borderRadius: 6, background: secondaryColor, border: '1px solid #ddd' }} />
                <div style={{ width: 80, height: 40, borderRadius: 6, background: accentColor }} />
              </div>

              <div className="form-group">
                <label>Estilo visual</label>
                <textarea className="form-control" rows={2} value={styleDescription} onChange={e => setStyleDescription(e.target.value)}
                  placeholder="Moderno e minimalista, fotos clean com bastante espaço em branco..." />
              </div>
            </div>
            <div className="card-footer d-flex justify-content-between">
              <button className="btn btn-outline-secondary" onClick={() => setStep(2)}>
                <i className="fas fa-arrow-left mr-1" /> Voltar
              </button>
              <div>
                <button className="btn btn-outline-secondary mr-2" onClick={() => setStep(4)}>Pular</button>
                <button className="btn btn-primary" onClick={saveStep3} disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm mr-1" /> : null}
                  Finalizar <i className="fas fa-check ml-1" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4 — Done */}
        {step === 4 && (
          <div className="card">
            <div className="card-body text-center py-5">
              <div
                className="rounded-circle mx-auto d-flex align-items-center justify-content-center mb-3"
                style={{ width: 80, height: 80, background: readiness && readiness.score >= 60 ? '#28a745' : '#ffc107', color: '#fff', fontSize: 32 }}
              >
                {readiness && readiness.score >= 60 ? <i className="fas fa-check" /> : <i className="fas fa-exclamation" />}
              </div>

              <h3>{readiness && readiness.score >= 60 ? 'Perfil configurado!' : 'Quase lá!'}</h3>
              <p className="text-muted">
                {readiness && readiness.score >= 60
                  ? 'Sua agência de marketing IA tem informações suficientes para começar a criar conteúdo.'
                  : 'Recomendamos completar mais campos para a IA gerar conteúdo de qualidade.'}
              </p>

              {/* Readiness bar */}
              <div className="mx-auto" style={{ maxWidth: 400 }}>
                <div className="d-flex justify-content-between mb-1">
                  <span className="font-weight-bold">{readiness?.score ?? 0}%</span>
                  <span className="text-muted small">{readiness?.filled_fields}/{readiness?.total_fields} campos</span>
                </div>
                <div className="progress mb-3" style={{ height: 12, borderRadius: 6 }}>
                  <div className={`progress-bar bg-${scoreColor}`} style={{ width: `${readiness?.score ?? 0}%`, borderRadius: 6 }} />
                </div>
              </div>

              {readiness && readiness.missing.length > 0 && (
                <div className="text-left mx-auto mb-4" style={{ maxWidth: 400 }}>
                  <p className="small font-weight-bold text-muted">Para melhorar a qualidade:</p>
                  {readiness.missing.map(m => (
                    <div key={m.field} className="d-flex align-items-center mb-1" style={{ fontSize: 13 }}>
                      <i className="fas fa-circle text-muted mr-2" style={{ fontSize: 6 }} />
                      <span>{m.label}</span>
                      <span className="badge badge-light ml-auto">+{m.weight}%</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="d-flex justify-content-center" style={{ gap: 12 }}>
                <button className="btn btn-outline-secondary" onClick={() => setStep(1)}>
                  <i className="fas fa-edit mr-1" /> Editar perfil
                </button>
                <button className="btn btn-primary btn-lg" onClick={onComplete}>
                  <i className="fas fa-magic mr-1" /> Começar a criar conteúdo
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
