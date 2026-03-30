import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { Business } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  steps?: AgentStep[]
}

interface AgentStep {
  agent: 'mara' | 'pixel' | 'luna'
  action: string
  status: 'done' | 'error'
}

const AGENT_COLORS: Record<string, { bg: string; label: string; icon: string }> = {
  sofia: { bg: '#6f42c1', label: 'Sofia', icon: 'fas fa-crown' },
  mara: { bg: '#007bff', label: 'Mara', icon: 'fas fa-share-alt' },
  pixel: { bg: '#e83e8c', label: 'Pixel', icon: 'fas fa-palette' },
  luna: { bg: '#fd7e14', label: 'Luna', icon: 'fas fa-ad' },
}

const QUICK_ACTIONS = [
  'Crie um post brandado para hoje',
  'Monte uma semana de conteúdo alinhada com minha marca',
  'Analise minha performance geral',
  'Me ajude a definir minha identidade de marca',
  'Quais posts estão esperando aprovação?',
  'Crie uma estratégia completa para o próximo mês',
]

export function AgencyPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState(() => localStorage.getItem('agency_biz') || '')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [activeStep, setActiveStep] = useState<string | null>(null)
  const [loadingMsg, setLoadingMsg] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) return
    localStorage.setItem('agency_biz', selectedBusiness)
    setHistoryLoading(true)
    setMessages([])
    api.agencyHistory(selectedBusiness)
      .then(r => setMessages(r.messages.map((m: { role: string; content: string }) => ({ ...m, steps: [] }))))
      .catch(console.error)
      .finally(() => setHistoryLoading(false))
  }, [selectedBusiness])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeStep])

  const send = async (text: string) => {
    if (!selectedBusiness || !text.trim() || loading) return
    const msgText = text.trim()
    const bizId = selectedBusiness
    const userMsg: Message = { role: 'user', content: msgText }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setActiveStep(null)
    const loadingMessages = [
      'Sofia está analisando sua marca...',
      'Preparando a melhor estratégia...',
      'Consultando a equipe criativa...',
      'Sofia está pensando no seu negócio...',
      'Analisando as melhores opções...',
    ]
    setLoadingMsg(loadingMessages[Math.floor(Math.random() * loadingMessages.length)])

    // Troca mensagem de loading a cada 8s para dar sensação de progresso
    const loadingTimer = setInterval(() => {
      setLoadingMsg(loadingMessages[Math.floor(Math.random() * loadingMessages.length)])
    }, 8000)

    try {
      const res = await api.agencyChat({ business_id: bizId, message: msgText })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response,
        steps: res.steps || [],
      }])
    } catch (e: any) {
      const errorMsg = e.message.includes('demorou demais')
        ? 'A Sofia está processando sua solicitação. Pode levar um momento — tente enviar "continua" em alguns segundos.'
        : `Erro: ${e.message}`
      setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }])
    } finally {
      clearInterval(loadingTimer)
      setLoading(false)
      setActiveStep(null)
    }
  }

  const clearHistory = async () => {
    if (!selectedBusiness) return
    if (!confirm('Limpar histórico desta conversa com Sofia?')) return
    await api.agencyClearHistory(selectedBusiness).catch(console.error)
    setMessages([])
  }

  const renderSteps = (steps: AgentStep[]) => {
    if (!steps || steps.length === 0) return null
    return (
      <div className="mt-2 mb-1">
        {steps.map((step, i) => {
          const agentInfo = AGENT_COLORS[step.agent] || AGENT_COLORS.sofia
          return (
            <div key={i} className="d-flex align-items-center mb-1" style={{ fontSize: 12 }}>
              <span
                className="badge mr-2"
                style={{ background: agentInfo.bg, color: '#fff', fontSize: 11, padding: '3px 8px' }}
              >
                <i className={`${agentInfo.icon} mr-1`} />
                {agentInfo.label}
              </span>
              <span className="text-muted">
                {step.action}
                {step.status === 'done'
                  ? <i className="fas fa-check-circle text-success ml-1" />
                  : <i className="fas fa-times-circle text-danger ml-1" />}
              </span>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="row">
      <div className="col-md-3">
        <div className="card" style={{ borderTop: '3px solid #6f42c1' }}>
          <div className="card-header" style={{ background: '#6f42c1', color: '#fff' }}>
            <h3 className="card-title"><i className="fas fa-crown mr-1" /> Sofia — Agência</h3>
          </div>
          <div className="card-body">
            <p className="text-muted small">
              Diretora Criativa da sua agência. Coordena Mara, Pixel e Luna para entregar resultados integrados.
            </p>

            <div className="d-flex mb-3" style={{ gap: 8 }}>
              {['mara', 'pixel', 'luna'].map(agent => {
                const info = AGENT_COLORS[agent]
                return (
                  <div key={agent} className="text-center" style={{ flex: 1 }}>
                    <div
                      className="rounded-circle mx-auto d-flex align-items-center justify-content-center"
                      style={{ width: 36, height: 36, background: info.bg, color: '#fff', fontSize: 14 }}
                    >
                      <i className={info.icon} />
                    </div>
                    <div style={{ fontSize: 10, marginTop: 2 }}>{info.label}</div>
                  </div>
                )
              })}
            </div>

            <div className="form-group">
              <label className="small font-weight-bold">Business</label>
              <select
                className="form-control form-control-sm"
                value={selectedBusiness}
                onChange={e => setSelectedBusiness(e.target.value)}
              >
                <option value="">Selecione...</option>
                {businesses.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>

            {selectedBusiness && (
              <>
                <p className="text-muted small font-weight-bold mt-3">Ações rápidas:</p>
                {QUICK_ACTIONS.map(action => (
                  <button
                    key={action}
                    className="btn btn-outline-secondary btn-sm btn-block mb-1 text-left"
                    onClick={() => send(action)}
                    disabled={loading}
                    style={{ fontSize: 12 }}
                  >
                    <i className="fas fa-bolt mr-1" style={{ color: '#6f42c1' }} />{action}
                  </button>
                ))}
                <hr />
                <button className="btn btn-sm btn-outline-danger btn-block" onClick={clearHistory}>
                  <i className="fas fa-trash mr-1" /> Limpar histórico
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="col-md-9">
        <div className="card" style={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ borderTop: '3px solid #6f42c1' }}>
            <h3 className="card-title">
              <i className="fas fa-crown mr-2" style={{ color: '#6f42c1' }} />
              {selectedBusiness
                ? `Agência — ${businesses.find(b => b.id === selectedBusiness)?.name ?? ''}`
                : 'Selecione um business para começar'}
            </h3>
          </div>

          <div className="card-body" style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
            {!selectedBusiness && (
              <div className="text-center text-muted mt-5">
                <i className="fas fa-crown fa-3x mb-3" style={{ opacity: 0.3, color: '#6f42c1' }} />
                <p>Selecione um business para conversar com a Sofia.</p>
                <p className="small">Ela coordena toda a equipe criativa: Mara, Pixel e Luna.</p>
              </div>
            )}

            {selectedBusiness && historyLoading && (
              <div className="text-center mt-4">
                <div className="spinner-border spinner-border-sm" style={{ color: '#6f42c1' }} />
              </div>
            )}

            {selectedBusiness && !historyLoading && messages.length === 0 && !loading && (
              <div className="text-center mt-4">
                <div
                  className="rounded-circle mx-auto d-flex align-items-center justify-content-center mb-3"
                  style={{ width: 64, height: 64, background: '#6f42c1', color: '#fff', fontSize: 24 }}
                >
                  S
                </div>
                <h5 style={{ color: '#6f42c1' }}>Olá! Eu sou a Sofia</h5>
                <p className="text-muted small mb-3" style={{ maxWidth: 400, margin: '0 auto' }}>
                  Sou a diretora criativa da sua agência. Vou conhecer seu negócio, entender sua marca e coordenar toda a estratégia de marketing.
                </p>
                <button
                  className="btn btn-lg"
                  style={{ background: '#6f42c1', color: '#fff', borderRadius: 12 }}
                  onClick={() => send('Olá Sofia! Quero configurar minha agência de marketing.')}
                >
                  <i className="fas fa-hand-sparkles mr-2" />Começar conversa
                </button>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`d-flex mb-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div
                    className="rounded-circle text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                    style={{ width: 32, height: 32, fontSize: 14, background: '#6f42c1' }}
                  >
                    S
                  </div>
                )}
                <div style={{ maxWidth: '75%' }}>
                  {msg.steps && msg.steps.length > 0 && renderSteps(msg.steps)}
                  <div
                    className="rounded p-3 small"
                    style={{
                      background: msg.role === 'user' ? '#6f42c1' : 'var(--bg-chat-msg)',
                      color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {msg.content}
                  </div>
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
                  className="rounded-circle text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                  style={{ width: 32, height: 32, fontSize: 14, background: '#6f42c1' }}
                >
                  S
                </div>
                <div className="rounded p-3 small" style={{ background: 'var(--bg-chat-msg)', color: 'var(--text-primary)' }}>
                  <span className="spinner-border spinner-border-sm mr-1" style={{ color: '#6f42c1' }} />
                  {loadingMsg || 'Sofia está pensando...'}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="card-footer">
            <div className="input-group">
              <input
                type="text"
                className="form-control"
                placeholder={selectedBusiness ? 'Fale com a Sofia...' : 'Selecione um business primeiro'}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
                disabled={!selectedBusiness || loading}
              />
              <div className="input-group-append">
                <button
                  className="btn"
                  style={{ background: '#6f42c1', color: '#fff', borderColor: '#6f42c1' }}
                  onClick={() => send(input)}
                  disabled={!selectedBusiness || !input.trim() || loading}
                >
                  <i className="fas fa-paper-plane" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
