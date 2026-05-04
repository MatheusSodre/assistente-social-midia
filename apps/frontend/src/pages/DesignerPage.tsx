import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { Business, VisualIdentity } from '../services/api'
import { ChatMessage } from '../components/ChatMessage'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function imgSrc(url?: string) {
  if (!url) return ''
  return url.startsWith('/') ? `${API_BASE}${url}` : url
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  image_url?: string
  uploaded_image?: string // local preview URL
}

const QUICK_ACTIONS = [
  'Qual é minha identidade visual atual?',
  'Remova o fundo desta imagem',
  'Adicione uma legenda no fundo da imagem',
  'Aplique o fundo da marca na imagem',
  'Me ajude a definir minha paleta de cores',
]

const DEFAULT_IDENTITY: VisualIdentity = {
  primary_color: '#000000',
  secondary_color: '#FFFFFF',
  accent_color: '#FF6B35',
  background_color: '#FFFFFF',
  text_color: '#000000',
  font_heading: 'Arial Bold',
  font_body: 'Arial',
  style_description: '',
  extra_context: '',
}

export function DesignerPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [pendingImage, setPendingImage] = useState<File | null>(null)
  const [pendingPreview, setPendingPreview] = useState<string | null>(null)
  const [identity, setIdentity] = useState<VisualIdentity>(DEFAULT_IDENTITY)
  const [identityLoading, setIdentityLoading] = useState(false)
  const [identitySaving, setIdentitySaving] = useState(false)
  const [identitySaved, setIdentitySaved] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) return
    setIdentityLoading(true)
    api.getVisualIdentity(selectedBusiness)
      .then(id => {
        if (id.found) setIdentity({ ...DEFAULT_IDENTITY, ...id })
        else setIdentity(DEFAULT_IDENTITY)
      })
      .catch(console.error)
      .finally(() => setIdentityLoading(false))
    setMessages([])
  }, [selectedBusiness])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const saveIdentity = async () => {
    if (!selectedBusiness) return
    setIdentitySaving(true)
    try {
      await api.updateVisualIdentity(selectedBusiness, identity)
      setIdentitySaved(true)
      setTimeout(() => setIdentitySaved(false), 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setIdentitySaving(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPendingImage(file)
    setPendingPreview(URL.createObjectURL(file))
    e.target.value = ''
  }

  const send = async (text: string) => {
    if (!selectedBusiness || (!text.trim() && !pendingImage) || loading) return
    const userMsg: Message = {
      role: 'user',
      content: text.trim() || 'Imagem enviada',
      uploaded_image: pendingPreview ?? undefined,
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    const imgToSend = pendingImage
    setPendingImage(null)
    setPendingPreview(null)
    setLoading(true)
    try {
      const res = await api.designerChat({
        business_id: selectedBusiness,
        message: text.trim() || 'O que você pode fazer com esta imagem?',
        image: imgToSend ?? undefined,
      })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response,
        image_url: res.image_url,
      }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Erro: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const ColorInput = ({ label, field }: { label: string; field: keyof VisualIdentity }) => (
    <div className="d-flex align-items-center mb-2" style={{ gap: 8 }}>
      <input
        type="color"
        value={(identity[field] as string) || '#000000'}
        onChange={e => setIdentity(prev => ({ ...prev, [field]: e.target.value }))}
        style={{ width: 32, height: 28, padding: 1, border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}
      />
      <span className="small" style={{ flex: 1 }}>{label}</span>
      <code className="small text-muted">{(identity[field] as string) || ''}</code>
    </div>
  )

  return (
    <div className="row">
      {/* Painel de Identidade Visual */}
      <div className="col-md-4">
        <div className="card card-warning">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-palette mr-1" /> Pixel</h3>
          </div>
          <div className="card-body" style={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}>
            <p className="text-muted small">Designer visual IA. Edita imagens, define identidade de marca e cria conteúdo brandado.</p>

            <div className="form-group">
              <label className="small font-weight-bold">Business</label>
              <select
                className="form-control form-control-sm"
                value={selectedBusiness}
                onChange={e => setSelectedBusiness(e.target.value)}
              >
                <option value="">Selecione...</option>
                {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>

            {selectedBusiness && (
              <>
                {/* Identidade Visual */}
                <div className="card card-outline card-secondary mt-2">
                  <div className="card-header p-2">
                    <h6 className="card-title mb-0 small font-weight-bold">
                      <i className="fas fa-paint-brush mr-1" />Identidade Visual
                    </h6>
                  </div>
                  <div className="card-body p-2">
                    {identityLoading ? (
                      <div className="text-center py-2"><span className="spinner-border spinner-border-sm" /></div>
                    ) : (
                      <>
                        <p className="small font-weight-bold text-muted mb-1">CORES</p>
                        <ColorInput label="Primária" field="primary_color" />
                        <ColorInput label="Secundária" field="secondary_color" />
                        <ColorInput label="Acento" field="accent_color" />
                        <ColorInput label="Fundo" field="background_color" />
                        <ColorInput label="Texto" field="text_color" />

                        <p className="small font-weight-bold text-muted mb-1 mt-2">TIPOGRAFIA</p>
                        <input
                          className="form-control form-control-sm mb-1"
                          placeholder="Fonte títulos (ex: Montserrat Bold)"
                          value={identity.font_heading || ''}
                          onChange={e => setIdentity(prev => ({ ...prev, font_heading: e.target.value }))}
                        />
                        <input
                          className="form-control form-control-sm mb-2"
                          placeholder="Fonte corpo (ex: Open Sans)"
                          value={identity.font_body || ''}
                          onChange={e => setIdentity(prev => ({ ...prev, font_body: e.target.value }))}
                        />

                        <p className="small font-weight-bold text-muted mb-1">ESTILO</p>
                        <textarea
                          className="form-control form-control-sm mb-1"
                          rows={2}
                          placeholder="Descreva o estilo (ex: minimalista, moderno, colorido...)"
                          value={identity.style_description || ''}
                          onChange={e => setIdentity(prev => ({ ...prev, style_description: e.target.value }))}
                        />
                        <textarea
                          className="form-control form-control-sm mb-2"
                          rows={2}
                          placeholder="Contexto extra: referências, o que evitar, diferenciais..."
                          value={identity.extra_context || ''}
                          onChange={e => setIdentity(prev => ({ ...prev, extra_context: e.target.value }))}
                        />

                        <button
                          className={`btn btn-sm btn-block ${identitySaved ? 'btn-success' : 'btn-warning'}`}
                          onClick={saveIdentity}
                          disabled={identitySaving}
                        >
                          {identitySaving
                            ? <span className="spinner-border spinner-border-sm mr-1" />
                            : <i className={`fas fa-${identitySaved ? 'check' : 'save'} mr-1`} />}
                          {identitySaved ? 'Salvo!' : 'Salvar identidade'}
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Ações rápidas */}
                <p className="text-muted small font-weight-bold mt-3 mb-1">Ações rápidas:</p>
                {QUICK_ACTIONS.map(action => (
                  <button
                    key={action}
                    className="btn btn-outline-secondary btn-sm btn-block mb-1 text-left"
                    onClick={() => send(action)}
                    disabled={loading}
                    style={{ fontSize: 12 }}
                  >
                    <i className="fas fa-bolt mr-1" />{action}
                  </button>
                ))}
                <hr />
                <button
                  className="btn btn-sm btn-outline-danger btn-block"
                  onClick={async () => {
                    if (!confirm('Limpar histórico?')) return
                    await api.designerClearHistory(selectedBusiness).catch(console.error)
                    setMessages([])
                  }}
                >
                  <i className="fas fa-trash mr-1" />Limpar histórico
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Chat */}
      <div className="col-md-8">
        <div className="card" style={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <h3 className="card-title">
              <i className="fas fa-magic mr-2" />
              {selectedBusiness
                ? `Pixel — ${businesses.find(b => b.id === selectedBusiness)?.name ?? ''}`
                : 'Selecione um business para começar'}
            </h3>
          </div>

          <div className="card-body" style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
            {!selectedBusiness && (
              <div className="text-center text-muted mt-5">
                <i className="fas fa-palette fa-3x mb-3" style={{ opacity: 0.3 }} />
                <p>Selecione um business para começar a criar com o Pixel.</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`d-flex mb-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                {msg.role === 'assistant' && (
                  <div
                    className="rounded-circle d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                    style={{ width: 32, height: 32, fontSize: 14, background: 'linear-gradient(135deg,#f093fb,#f5576c)', color: '#fff' }}
                  >
                    P
                  </div>
                )}
                <div style={{ maxWidth: '75%' }}>
                  {/* Imagem enviada pelo usuário */}
                  {msg.uploaded_image && (
                    <div className="mb-1">
                      <img src={msg.uploaded_image} alt="upload" style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 8, display: 'block' }} />
                    </div>
                  )}
                  <div
                    className="rounded p-3 small"
                    style={{
                      background: msg.role === 'user' ? '#007bff' : 'var(--bg-chat-msg)',
                      color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                      wordBreak: 'break-word',
                      ...(msg.role === 'user' ? { whiteSpace: 'pre-wrap' as const } : {}),
                    }}
                  >
                    <ChatMessage content={msg.content} role={msg.role} />
                  </div>
                  {/* Imagem resultado do agente */}
                  {msg.image_url && (
                    <div className="mt-2">
                      <img
                        src={imgSrc(msg.image_url)}
                        alt="resultado"
                        style={{ maxWidth: '100%', borderRadius: 8, display: 'block', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                      />
                      <a
                        href={imgSrc(msg.image_url)}
                        download
                        className="btn btn-xs btn-outline-secondary mt-1"
                        style={{ fontSize: 11 }}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <i className="fas fa-download mr-1" />Download
                      </a>
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div
                    className="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center ml-2 flex-shrink-0"
                    style={{ width: 32, height: 32, fontSize: 14 }}
                  >
                    U
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="d-flex justify-content-start mb-3">
                <div
                  className="rounded-circle d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                  style={{ width: 32, height: 32, fontSize: 14, background: 'linear-gradient(135deg,#f093fb,#f5576c)', color: '#fff' }}
                >
                  P
                </div>
                <div className="rounded p-3 small" style={{ background: 'var(--bg-chat-msg)', color: 'var(--text-primary)' }}>
                  <span className="spinner-border spinner-border-sm mr-1" />
                  Pixel está criando...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="card-footer">
            {/* Preview de imagem pendente */}
            {pendingPreview && (
              <div className="mb-2 d-flex align-items-center" style={{ gap: 8 }}>
                <img src={pendingPreview} alt="preview" style={{ height: 48, borderRadius: 4, objectFit: 'cover' }} />
                <span className="small text-muted">{pendingImage?.name}</span>
                <button className="btn btn-xs btn-outline-danger ml-auto" onClick={() => { setPendingImage(null); setPendingPreview(null) }}>
                  <i className="fas fa-times" />
                </button>
              </div>
            )}
            <div className="input-group">
              <div className="input-group-prepend">
                <button
                  className="btn btn-outline-secondary"
                  title="Enviar imagem"
                  onClick={() => fileRef.current?.click()}
                  disabled={!selectedBusiness || loading}
                >
                  <i className="fas fa-image" />
                </button>
              </div>
              <input
                type="text"
                className="form-control"
                placeholder={selectedBusiness ? 'Descreva o que quer fazer...' : 'Selecione um business primeiro'}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
                disabled={!selectedBusiness || loading}
              />
              <div className="input-group-append">
                <button
                  className="btn btn-warning"
                  onClick={() => send(input)}
                  disabled={!selectedBusiness || (!input.trim() && !pendingImage) || loading}
                >
                  <i className="fas fa-paper-plane" />
                </button>
              </div>
            </div>
            <input type="file" ref={fileRef} accept="image/*" style={{ display: 'none' }} onChange={handleFileChange} />
          </div>
        </div>
      </div>
    </div>
  )
}
