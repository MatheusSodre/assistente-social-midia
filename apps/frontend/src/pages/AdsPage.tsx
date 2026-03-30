import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { Business, AdsAccount, AdsAccountConnect } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const QUICK_ACTIONS = [
  'Mostre um overview da minha conta',
  'Liste todas as campanhas',
  'Quais são minhas melhores palavras-chave?',
  'Analise minha performance e dê recomendações',
  'Sugira keywords para [produto/serviço]',
]

export function AdsPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [adsAccount, setAdsAccount] = useState<AdsAccount | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'config'>('chat')

  // Config form state
  const [configForm, setConfigForm] = useState<AdsAccountConnect>({
    business_id: '',
    customer_id: '',
    refresh_token: '',
    login_customer_id: '',
    is_test_account: true,
  })
  const [configLoading, setConfigLoading] = useState(false)
  const [configMsg, setConfigMsg] = useState('')

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) {
      setAdsAccount(null)
      setMessages([])
      return
    }
    setConfigForm(prev => ({ ...prev, business_id: selectedBusiness }))

    // Load ads account status
    api.getAdsAccount(selectedBusiness)
      .then(setAdsAccount)
      .catch(() => setAdsAccount({ connected: false }))

    // Load chat history
    setHistoryLoading(true)
    api.lunaHistory(selectedBusiness)
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
      const res = await api.lunaChat({ business_id: selectedBusiness, message: text.trim() })
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro desconhecido'
      setMessages(prev => [...prev, { role: 'assistant', content: `Erro: ${msg}` }])
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = async () => {
    if (!selectedBusiness) return
    if (!confirm('Limpar histórico desta conversa com a Luna?')) return
    await api.lunaClearHistory(selectedBusiness).catch(console.error)
    setMessages([])
  }

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault()
    setConfigLoading(true)
    setConfigMsg('')
    try {
      await api.connectAdsAccount(configForm)
      setConfigMsg('Conta conectada com sucesso!')
      const updated = await api.getAdsAccount(selectedBusiness)
      setAdsAccount(updated)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao conectar'
      setConfigMsg(`Erro: ${msg}`)
    } finally {
      setConfigLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!selectedBusiness) return
    if (!confirm('Desconectar conta Google Ads?')) return
    try {
      await api.disconnectAdsAccount(selectedBusiness)
      setAdsAccount({ connected: false })
      setConfigMsg('Conta desconectada.')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao desconectar'
      setConfigMsg(`Erro: ${msg}`)
    }
  }

  const businessName = businesses.find(b => b.id === selectedBusiness)?.name ?? ''

  return (
    <div className="row">
      {/* Left panel */}
      <div className="col-md-3">
        <div className="card card-warning">
          <div className="card-header">
            <h3 className="card-title"><i className="fab fa-google mr-1" /> Luna — Google Ads</h3>
          </div>
          <div className="card-body">
            <p className="text-muted small">
              Especialista em Google Ads com 8 anos de experiência. Analisa campanhas, otimiza orçamentos e sugere keywords.
            </p>

            {/* Account status badge */}
            {selectedBusiness && adsAccount && (
              <div className={`alert alert-${adsAccount.connected ? 'success' : 'warning'} py-1 px-2 small mb-2`}>
                {adsAccount.connected ? (
                  <><i className="fas fa-check-circle mr-1" /> Conta conectada: {adsAccount.customer_id}</>
                ) : (
                  <><i className="fas fa-exclamation-triangle mr-1" /> Conta não conectada — dados demonstrativos</>
                )}
              </div>
            )}

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

            {selectedBusiness && activeTab === 'chat' && (
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

      {/* Right panel */}
      <div className="col-md-9">
        <div className="card">
          <div className="card-header p-0 border-bottom-0">
            <ul className="nav nav-tabs" id="luna-tabs">
              <li className="nav-item">
                <a
                  className={`nav-link ${activeTab === 'chat' ? 'active' : ''}`}
                  href="#"
                  onClick={e => { e.preventDefault(); setActiveTab('chat') }}
                >
                  <i className="fas fa-comments mr-1" /> Luna (Chat)
                </a>
              </li>
              <li className="nav-item">
                <a
                  className={`nav-link ${activeTab === 'config' ? 'active' : ''}`}
                  href="#"
                  onClick={e => { e.preventDefault(); setActiveTab('config') }}
                >
                  <i className="fas fa-cog mr-1" /> Configurar Conta
                </a>
              </li>
            </ul>
          </div>

          {/* Chat Tab */}
          {activeTab === 'chat' && (
            <>
              <div className="card-header border-top-0">
                <h3 className="card-title">
                  <i className="fas fa-comments mr-2" />
                  {selectedBusiness
                    ? `Conversa com Luna — ${businessName}`
                    : 'Selecione um business para começar'}
                </h3>
              </div>

              <div className="card-body" style={{ height: 'calc(100vh - 320px)', overflowY: 'auto', padding: '1rem' }}>
                {!selectedBusiness && (
                  <div className="text-center text-muted mt-5">
                    <i className="fab fa-google fa-3x mb-3" style={{ opacity: 0.3 }} />
                    <p>Selecione um business no painel ao lado para conversar com a Luna.</p>
                  </div>
                )}

                {selectedBusiness && historyLoading && (
                  <div className="text-center mt-4">
                    <div className="spinner-border spinner-border-sm text-warning" />
                  </div>
                )}

                {selectedBusiness && !historyLoading && messages.length === 0 && (
                  <div className="text-center text-muted mt-5">
                    <i className="fas fa-chart-bar fa-2x mb-2" style={{ opacity: 0.3 }} />
                    <p className="small">Nenhuma mensagem ainda. Pergunte à Luna sobre suas campanhas!</p>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`d-flex mb-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div
                        className="rounded-circle bg-warning text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                        style={{ width: 32, height: 32, fontSize: 14 }}
                      >
                        L
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
                      className="rounded-circle bg-warning text-white d-flex align-items-center justify-content-center mr-2 flex-shrink-0"
                      style={{ width: 32, height: 32, fontSize: 14 }}
                    >
                      L
                    </div>
                    <div className="rounded p-3 small" style={{ background: 'var(--bg-chat-msg)', color: 'var(--text-primary)' }}>
                      <span className="spinner-border spinner-border-sm mr-1" />
                      Luna está analisando...
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
                      className="btn btn-warning"
                      onClick={() => send(input)}
                      disabled={!selectedBusiness || !input.trim() || loading}
                    >
                      <i className="fas fa-paper-plane" />
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Config Tab */}
          {activeTab === 'config' && (
            <>
              <div className="card-header border-top-0">
                <h3 className="card-title">
                  <i className="fab fa-google mr-2" /> Conectar Conta Google Ads
                </h3>
              </div>
              <div className="card-body">
                {!selectedBusiness ? (
                  <div className="alert alert-info">
                    <i className="fas fa-info-circle mr-1" /> Selecione um business no painel ao lado para configurar a conta Google Ads.
                  </div>
                ) : (
                  <>
                    {adsAccount?.connected && (
                      <div className="alert alert-success">
                        <strong><i className="fas fa-check-circle mr-1" /> Conta conectada</strong><br />
                        Customer ID: <code>{adsAccount.customer_id}</code>
                        {adsAccount.is_test_account && <span className="badge badge-warning ml-2">Conta de Teste</span>}
                        <br />
                        <button
                          className="btn btn-sm btn-outline-danger mt-2"
                          onClick={handleDisconnect}
                        >
                          <i className="fas fa-unlink mr-1" /> Desconectar
                        </button>
                      </div>
                    )}

                    {configMsg && (
                      <div className={`alert ${configMsg.startsWith('Erro') ? 'alert-danger' : 'alert-success'} py-2`}>
                        {configMsg}
                      </div>
                    )}

                    <form onSubmit={handleConnect}>
                      <div className="form-group">
                        <label className="font-weight-bold">Customer ID <span className="text-danger">*</span></label>
                        <input
                          type="text"
                          className="form-control"
                          placeholder="ex: 1234567890 (sem hífens)"
                          value={configForm.customer_id}
                          onChange={e => setConfigForm(prev => ({ ...prev, customer_id: e.target.value }))}
                          required
                        />
                        <small className="text-muted">ID da conta Google Ads, sem hífens.</small>
                      </div>

                      <div className="form-group">
                        <label className="font-weight-bold">Refresh Token <span className="text-danger">*</span></label>
                        <input
                          type="password"
                          className="form-control"
                          placeholder="OAuth2 Refresh Token"
                          value={configForm.refresh_token}
                          onChange={e => setConfigForm(prev => ({ ...prev, refresh_token: e.target.value }))}
                          required
                        />
                        <small className="text-muted">Token OAuth2 para autenticação na API Google Ads.</small>
                      </div>

                      <div className="form-group">
                        <label className="font-weight-bold">Login Customer ID (MCC)</label>
                        <input
                          type="text"
                          className="form-control"
                          placeholder="ex: 9876543210 (opcional)"
                          value={configForm.login_customer_id ?? ''}
                          onChange={e => setConfigForm(prev => ({ ...prev, login_customer_id: e.target.value || undefined }))}
                        />
                        <small className="text-muted">ID da conta gerenciadora (MCC), se aplicável.</small>
                      </div>

                      <div className="form-group">
                        <div className="custom-control custom-checkbox">
                          <input
                            type="checkbox"
                            className="custom-control-input"
                            id="isTestAccount"
                            checked={configForm.is_test_account}
                            onChange={e => setConfigForm(prev => ({ ...prev, is_test_account: e.target.checked }))}
                          />
                          <label className="custom-control-label" htmlFor="isTestAccount">
                            Conta de teste (Google Ads Test Account)
                          </label>
                        </div>
                      </div>

                      <button
                        type="submit"
                        className="btn btn-warning"
                        disabled={configLoading || !configForm.customer_id || !configForm.refresh_token}
                      >
                        {configLoading
                          ? <><span className="spinner-border spinner-border-sm mr-1" /> Conectando...</>
                          : <><i className="fab fa-google mr-1" /> {adsAccount?.connected ? 'Atualizar Conta' : 'Conectar Conta'}</>
                        }
                      </button>
                    </form>

                    <hr />
                    <div className="card card-outline card-secondary">
                      <div className="card-header py-2">
                        <h3 className="card-title small font-weight-bold">Como obter as credenciais</h3>
                      </div>
                      <div className="card-body small text-muted">
                        <ol className="pl-3 mb-0">
                          <li>Acesse o <a href="https://developers.google.com/google-ads/api/docs/oauth/overview" target="_blank" rel="noopener noreferrer">Google Ads API OAuth Guide</a></li>
                          <li>Crie um projeto no Google Cloud Console e ative a Google Ads API</li>
                          <li>Gere as credenciais OAuth2 (Client ID + Client Secret)</li>
                          <li>Use o <code>generate_user_credentials.py</code> do SDK para obter o Refresh Token</li>
                          <li>Configure <code>GOOGLE_ADS_DEVELOPER_TOKEN</code>, <code>GOOGLE_ADS_CLIENT_ID</code> e <code>GOOGLE_ADS_CLIENT_SECRET</code> no .env do backend</li>
                        </ol>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
