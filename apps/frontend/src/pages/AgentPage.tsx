import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { Business } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const QUICK_ACTIONS = [
  'Crie um post para hoje',
  'Monte uma semana de conteúdo',
  'Quais posts estão esperando aprovação?',
  'Analise minha performance',
  'Sugira um calendário para os próximos 7 dias',
]

export function AgentPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) return
    setHistoryLoading(true)
    api.agentHistory(selectedBusiness)
      .then(r => setMessages(r.messages))
      .catch(console.error)
      .finally(() => setHistoryLoading(false))
  }, [selectedBusiness])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text: string) => {
    if (!selectedBusiness || !text.trim() || loading) return
    const userMsg: Message = { role: 'user', content: text.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await api.agentChat({ business_id: selectedBusiness, message: text.trim() })
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Erro: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = async () => {
    if (!selectedBusiness) return
    if (!confirm('Limpar histórico desta conversa?')) return
    await api.agentClearHistory(selectedBusiness).catch(console.error)
    setMessages([])
  }

  return (
    <div className="row">
      <div className="col-md-3">
        <div className="card card-primary">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-robot mr-1" /> Mara</h3>
          </div>
          <div className="card-body">
            <p className="text-muted small">
              Sua especialista sênior em Social Media. Cria conteúdo, analisa métricas e planeja sua estratégia.
            </p>
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
                  >
                    <i className="fas fa-bolt mr-1" />{action}
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
          <div className="card-header">
            <h3 className="card-title">
              <i className="fas fa-comments mr-2" />
              {selectedBusiness
                ? `Conversa com Mara — ${businesses.find(b => b.id === selectedBusiness)?.name ?? ''}`
                : 'Selecione um business para começar'}
            </h3>
          </div>

          <div className="card-body" style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
            {!selectedBusiness && (
              <div className="text-center text-muted mt-5">
                <i className="fas fa-robot fa-3x mb-3" style={{ opacity: 0.3 }} />
                <p>Selecione um business no painel ao lado para conversar com a Mara.</p>
              </div>
            )}

            {selectedBusiness && historyLoading && (
              <div className="text-center mt-4">
                <div className="spinner-border spinner-border-sm text-primary" />
              </div>
            )}

            {selectedBusiness && !historyLoading && messages.length === 0 && (
              <div className="text-center text-muted mt-5">
                <i className="fas fa-comments fa-2x mb-2" style={{ opacity: 0.3 }} />
                <p className="small">Nenhuma mensagem ainda. Diga olá para a Mara!</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`d-flex mb-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div
                    className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                    style={{ width: 32, height: 32, fontSize: 14 }}
                  >
                    M
                  </div>
                )}
                <div
                  className="rounded p-3 small"
                  style={{
                    maxWidth: '75%',
                    background: msg.role === 'user' ? '#007bff' : 'var(--bg-chat-msg)',
                    color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {msg.content}
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
                  className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                  style={{ width: 32, height: 32, fontSize: 14 }}
                >
                  M
                </div>
                <div className="rounded p-3 small" style={{ background: 'var(--bg-chat-msg)', color: 'var(--text-primary)' }}>
                  <span className="spinner-border spinner-border-sm mr-1" />
                  Mara está pensando...
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
                placeholder={selectedBusiness ? 'Digite sua mensagem...' : 'Selecione um business primeiro'}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
                disabled={!selectedBusiness || loading}
              />
              <div className="input-group-append">
                <button
                  className="btn btn-primary"
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
