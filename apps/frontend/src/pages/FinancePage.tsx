import { useCallback, useEffect, useRef, useState } from 'react'
import {
  api,
  type FinanceAlert,
  type FinanceAnalysis,
  type FinanceConnection,
  type FinanceTransaction,
} from '../services/api'

declare global {
  interface Window {
    PluggyConnect?: new (config: {
      connectToken: string
      onSuccess: (data: { item: { id: string; connector: { name: string } } }) => void
      onError: (err: unknown) => void
      onClose: () => void
    }) => { open: () => void }
  }
}

export function FinancePage() {
  const [connections, setConnections] = useState<FinanceConnection[]>([])
  const [transactions, setTransactions] = useState<FinanceTransaction[]>([])
  const [analysis, setAnalysis] = useState<FinanceAnalysis | null>(null)
  const [alerts, setAlerts] = useState<FinanceAlert[]>([])

  const [loadingConnections, setLoadingConnections] = useState(true)
  const [loadingTxs, setLoadingTxs] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [loadingSync, setLoadingSync] = useState(false)
  const [connectingWidget, setConnectingWidget] = useState(false)

  const [filterDays, setFilterDays] = useState(30)
  const [filterTipo, setFilterTipo] = useState('')
  const [filterBusca, setFilterBusca] = useState('')
  const [txPage, setTxPage] = useState(1)

  const [error, setError] = useState('')
  const [syncMsg, setSyncMsg] = useState('')

  const pluggyScriptLoaded = useRef(false)

  // ─── Load Pluggy SDK ──────────────────────────────────────────────────────

  useEffect(() => {
    if (pluggyScriptLoaded.current) return
    const script = document.createElement('script')
    script.src = 'https://cdn.pluggy.ai/pluggy-connect/v2.1.0/pluggy-connect.js'
    script.async = true
    document.head.appendChild(script)
    pluggyScriptLoaded.current = true
  }, [])

  // ─── Data fetching ────────────────────────────────────────────────────────

  const fetchConnections = useCallback(async () => {
    setLoadingConnections(true)
    try {
      const data = await api.financeListConnections()
      setConnections(data)
    } catch {
      setError('Erro ao carregar conexões bancárias')
    } finally {
      setLoadingConnections(false)
    }
  }, [])

  const fetchTransactions = useCallback(async () => {
    setLoadingTxs(true)
    try {
      const data = await api.financeTransactions({
        days: filterDays,
        tipo: filterTipo || undefined,
        busca: filterBusca || undefined,
      })
      setTransactions(data)
      setTxPage(1)
    } catch {
      setError('Erro ao carregar transações')
    } finally {
      setLoadingTxs(false)
    }
  }, [filterDays, filterTipo, filterBusca])

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await api.financeAlerts(7)
      setAlerts(data)
    } catch {
      // silencioso
    }
  }, [])

  useEffect(() => {
    fetchConnections()
    fetchAlerts()
  }, [fetchConnections, fetchAlerts])

  useEffect(() => {
    if (connections.length > 0) {
      fetchTransactions()
    }
  }, [connections.length, fetchTransactions])

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function openPluggyWidget() {
    setConnectingWidget(true)
    setError('')
    try {
      const { connect_token } = await api.financeConnectToken()

      if (!window.PluggyConnect) {
        setError('SDK Pluggy não carregado. Aguarde alguns segundos e tente novamente.')
        return
      }

      const widget = new window.PluggyConnect({
        connectToken: connect_token,
        onSuccess: async ({ item }) => {
          try {
            await api.financeCreateConnection({ item_id: item.id, connector_name: item.connector?.name })
            await fetchConnections()
            setSyncMsg('Banco conectado! Sincronizando transações...')
            setTimeout(() => setSyncMsg(''), 5000)
          } catch {
            setError('Erro ao salvar conexão bancária')
          }
        },
        onError: (err) => {
          console.error('Pluggy error:', err)
          setError('Erro ao conectar com o banco')
        },
        onClose: () => setConnectingWidget(false),
      })

      widget.open()
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Erro ao iniciar conexão: ${msg}`)
    } finally {
      setConnectingWidget(false)
    }
  }

  async function handleDisconnect(id: string) {
    if (!confirm('Remover esta conexão bancária? Todas as transações associadas serão apagadas.')) return
    try {
      await api.financeDeleteConnection(id)
      await fetchConnections()
      setTransactions([])
    } catch {
      setError('Erro ao remover conexão')
    }
  }

  async function handleSync() {
    setLoadingSync(true)
    setSyncMsg('')
    setError('')
    try {
      const result = await api.financeSync()
      setSyncMsg(`Sincronizados: ${result.synced} conta(s)${result.errors.length ? ` | Erros: ${result.errors.length}` : ''}`)
      await fetchConnections()
      await fetchTransactions()
      await fetchAlerts()
    } catch {
      setError('Erro ao sincronizar')
    } finally {
      setLoadingSync(false)
      setTimeout(() => setSyncMsg(''), 6000)
    }
  }

  async function handleAnalysis() {
    setLoadingAnalysis(true)
    setAnalysis(null)
    setError('')
    try {
      const data = await api.financeAnalysis()
      setAnalysis(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Erro na análise: ${msg}`)
    } finally {
      setLoadingAnalysis(false)
    }
  }

  // ─── Pagination ───────────────────────────────────────────────────────────

  const PAGE_SIZE = 20
  const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE))
  const pagedTxs = transactions.slice((txPage - 1) * PAGE_SIZE, txPage * PAGE_SIZE)

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div>
      {error && (
        <div className="alert alert-danger alert-dismissible">
          <button type="button" className="close" onClick={() => setError('')}>
            <span>&times;</span>
          </button>
          {error}
        </div>
      )}
      {syncMsg && (
        <div className="alert alert-success alert-dismissible">
          <button type="button" className="close" onClick={() => setSyncMsg('')}>
            <span>&times;</span>
          </button>
          {syncMsg}
        </div>
      )}

      {/* ── Contas Conectadas ── */}
      <div className="card card-primary card-outline">
        <div className="card-header d-flex align-items-center justify-content-between">
          <h3 className="card-title mb-0">
            <i className="fas fa-university mr-2" />
            Contas Conectadas
          </h3>
          <div className="d-flex" style={{ gap: 8 }}>
            {connections.length > 0 && (
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={handleSync}
                disabled={loadingSync}
              >
                {loadingSync
                  ? <><i className="fas fa-spinner fa-spin mr-1" />Sincronizando...</>
                  : <><i className="fas fa-sync mr-1" />Sincronizar</>
                }
              </button>
            )}
            <button
              className="btn btn-sm btn-primary"
              onClick={openPluggyWidget}
              disabled={connectingWidget}
            >
              {connectingWidget
                ? <><i className="fas fa-spinner fa-spin mr-1" />Abrindo...</>
                : <><i className="fas fa-plus mr-1" />Conectar banco</>
              }
            </button>
          </div>
        </div>
        <div className="card-body">
          {loadingConnections ? (
            <div className="text-center py-3">
              <i className="fas fa-spinner fa-spin fa-2x text-muted" />
            </div>
          ) : connections.length === 0 ? (
            <div className="text-center text-muted py-4">
              <i className="fas fa-university fa-3x mb-3 d-block" style={{ opacity: 0.3 }} />
              <p>Nenhuma conta conectada. Clique em <strong>Conectar banco</strong> para começar.</p>
            </div>
          ) : (
            <div className="row">
              {connections.map(conn => (
                <div key={conn.id} className="col-md-4 col-sm-6 mb-3">
                  <div className="card card-widget widget-user-2 mb-0 shadow-sm">
                    <div className="card-footer p-3">
                      <div className="d-flex align-items-center justify-content-between">
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 15 }}>
                            <i className="fas fa-university mr-2 text-primary" />
                            {conn.connector_name ?? 'Banco desconhecido'}
                          </div>
                          <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                            {conn.status === 'updated' && (
                              <span className="badge badge-success">Atualizado</span>
                            )}
                            {conn.status === 'updating' && (
                              <span className="badge badge-warning">Sincronizando</span>
                            )}
                            {conn.status === 'error' && (
                              <span className="badge badge-danger">Erro</span>
                            )}
                            {conn.last_synced_at && (
                              <span className="ml-2">
                                {new Date(conn.last_synced_at).toLocaleDateString('pt-BR')}
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          className="btn btn-sm btn-outline-danger"
                          title="Remover conexão"
                          onClick={() => handleDisconnect(conn.id)}
                        >
                          <i className="fas fa-trash" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Alertas de Vencimento ── */}
      {alerts.length > 0 && (
        <div className="card card-warning card-outline">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fas fa-bell mr-2 text-warning" />
              Vencimentos Próximos (7 dias)
            </h3>
          </div>
          <div className="card-body p-0">
            <ul className="list-group list-group-flush">
              {alerts.map(alert => (
                <li key={alert.id} className="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <span className="font-weight-bold">{alert.description}</span>
                    {alert.date && (
                      <span className="text-muted ml-2" style={{ fontSize: 12 }}>
                        {new Date(alert.date).toLocaleDateString('pt-BR')}
                      </span>
                    )}
                  </div>
                  <div className="d-flex align-items-center" style={{ gap: 8 }}>
                    {alert.amount != null && (
                      <span className="font-weight-bold text-danger">
                        R$ {Math.abs(alert.amount).toFixed(2).replace('.', ',')}
                      </span>
                    )}
                    <span className={`badge ${alert.days_until_due <= 1 ? 'badge-danger' : 'badge-warning'}`}>
                      {alert.days_until_due === 0 ? 'Hoje' : `${alert.days_until_due}d`}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* ── Extrato ── */}
      {connections.length > 0 && (
        <div className="card card-outline card-info">
          <div className="card-header d-flex align-items-center justify-content-between flex-wrap" style={{ gap: 8 }}>
            <h3 className="card-title mb-0">
              <i className="fas fa-list-alt mr-2" />
              Extrato
              {transactions.length > 0 && (
                <span className="badge badge-secondary ml-2">{transactions.length}</span>
              )}
            </h3>
            <div className="d-flex flex-wrap align-items-center" style={{ gap: 8 }}>
              <select
                className="form-control form-control-sm"
                value={filterDays}
                onChange={e => setFilterDays(Number(e.target.value))}
                style={{ width: 130 }}
              >
                <option value={7}>Últimos 7 dias</option>
                <option value={15}>Últimos 15 dias</option>
                <option value={30}>Últimos 30 dias</option>
                <option value={60}>Últimos 60 dias</option>
                <option value={90}>Últimos 90 dias</option>
              </select>
              <select
                className="form-control form-control-sm"
                value={filterTipo}
                onChange={e => setFilterTipo(e.target.value)}
                style={{ width: 110 }}
              >
                <option value="">Todos</option>
                <option value="CREDIT">Crédito</option>
                <option value="DEBIT">Débito</option>
              </select>
              <input
                type="text"
                className="form-control form-control-sm"
                placeholder="Buscar descrição..."
                value={filterBusca}
                onChange={e => setFilterBusca(e.target.value)}
                style={{ width: 200 }}
              />
              <button
                className="btn btn-sm btn-info"
                onClick={fetchTransactions}
                disabled={loadingTxs}
              >
                {loadingTxs ? <i className="fas fa-spinner fa-spin" /> : <i className="fas fa-search" />}
              </button>
            </div>
          </div>
          <div className="card-body p-0">
            {loadingTxs ? (
              <div className="text-center py-4">
                <i className="fas fa-spinner fa-spin fa-2x text-muted" />
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center text-muted py-4">
                Nenhuma transação encontrada para o período selecionado.
              </div>
            ) : (
              <>
                <div className="table-responsive">
                  <table className="table table-sm table-hover table-striped mb-0">
                    <thead className="thead-light">
                      <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                        <th>Categoria</th>
                        <th className="text-right">Valor</th>
                        <th>Tipo</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pagedTxs.map(tx => (
                        <tr key={tx.id}>
                          <td style={{ whiteSpace: 'nowrap', fontSize: 13 }}>
                            {tx.date ? new Date(tx.date).toLocaleDateString('pt-BR') : '—'}
                          </td>
                          <td style={{ fontSize: 13, maxWidth: 280 }}>
                            <span title={tx.description ?? ''}>{tx.description ?? '—'}</span>
                          </td>
                          <td style={{ fontSize: 12 }}>
                            {tx.category ? (
                              <span className="badge badge-light border">{tx.category}</span>
                            ) : '—'}
                          </td>
                          <td className="text-right" style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                            <span className={tx.type === 'CREDIT' ? 'text-success' : 'text-danger'}>
                              {tx.type === 'CREDIT' ? '+' : '-'}
                              {tx.amount != null ? `R$ ${Math.abs(tx.amount).toFixed(2).replace('.', ',')}` : '—'}
                            </span>
                          </td>
                          <td>
                            {tx.type === 'CREDIT'
                              ? <span className="badge badge-success">Crédito</span>
                              : <span className="badge badge-danger">Débito</span>
                            }
                          </td>
                          <td>
                            {tx.status === 'PENDING'
                              ? <span className="badge badge-warning">Pendente</span>
                              : <span className="badge badge-secondary">Postado</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {totalPages > 1 && (
                  <div className="card-footer d-flex justify-content-between align-items-center">
                    <span className="text-muted" style={{ fontSize: 13 }}>
                      Página {txPage} de {totalPages} — {transactions.length} transações
                    </span>
                    <div className="btn-group btn-group-sm">
                      <button
                        className="btn btn-outline-secondary"
                        disabled={txPage === 1}
                        onClick={() => setTxPage(p => p - 1)}
                      >
                        <i className="fas fa-chevron-left" />
                      </button>
                      <button
                        className="btn btn-outline-secondary"
                        disabled={txPage === totalPages}
                        onClick={() => setTxPage(p => p + 1)}
                      >
                        <i className="fas fa-chevron-right" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Análise IA ── */}
      {connections.length > 0 && (
        <div className="card card-outline card-success">
          <div className="card-header d-flex align-items-center justify-content-between">
            <h3 className="card-title mb-0">
              <i className="fas fa-brain mr-2 text-success" />
              Análise IA — Últimos 30 dias
            </h3>
            <button
              className="btn btn-sm btn-success"
              onClick={handleAnalysis}
              disabled={loadingAnalysis}
            >
              {loadingAnalysis
                ? <><i className="fas fa-spinner fa-spin mr-1" />Analisando...</>
                : <><i className="fas fa-robot mr-1" />Analisar com IA</>
              }
            </button>
          </div>
          <div className="card-body">
            {!analysis && !loadingAnalysis && (
              <p className="text-muted text-center py-2">
                Clique em <strong>Analisar com IA</strong> para obter insights sobre seus gastos.
              </p>
            )}
            {loadingAnalysis && (
              <div className="text-center py-4">
                <i className="fas fa-spinner fa-spin fa-2x text-success mb-2 d-block" />
                <small className="text-muted">Claude está analisando suas transações...</small>
              </div>
            )}
            {analysis && (
              <div>
                {/* Resumo */}
                <div className="callout callout-success">
                  <p className="mb-0">{analysis.summary}</p>
                </div>

                <div className="row mt-3">
                  {/* Top categorias */}
                  {analysis.top_categories.length > 0 && (
                    <div className="col-md-5">
                      <h6 className="font-weight-bold">Top Categorias</h6>
                      {analysis.top_categories.slice(0, 6).map((cat, i) => (
                        <div key={i} className="mb-2">
                          <div className="d-flex justify-content-between mb-1">
                            <span style={{ fontSize: 13 }}>{cat.category}</span>
                            <span style={{ fontSize: 13, fontWeight: 600 }}>
                              R$ {Number(cat.total).toFixed(2).replace('.', ',')}
                            </span>
                          </div>
                          <div className="progress" style={{ height: 6 }}>
                            <div
                              className="progress-bar bg-success"
                              style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Insights + Recomendações */}
                  <div className={analysis.top_categories.length > 0 ? 'col-md-7' : 'col-12'}>
                    {analysis.insights.length > 0 && (
                      <div className="mb-3">
                        <h6 className="font-weight-bold">
                          <i className="fas fa-lightbulb mr-1 text-warning" />
                          Insights
                        </h6>
                        <ul className="pl-3 mb-0" style={{ fontSize: 13 }}>
                          {analysis.insights.map((ins, i) => <li key={i}>{ins}</li>)}
                        </ul>
                      </div>
                    )}
                    {analysis.recommendations.length > 0 && (
                      <div>
                        <h6 className="font-weight-bold">
                          <i className="fas fa-check-circle mr-1 text-success" />
                          Recomendações
                        </h6>
                        <ul className="pl-3 mb-0" style={{ fontSize: 13 }}>
                          {analysis.recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
