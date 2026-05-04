import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { HistoryPost } from '../services/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
function imgSrc(url?: string) {
  if (!url) return ''
  return url.startsWith('/') ? `${API_BASE}${url}` : url
}

export function HistoryPage() {
  const [posts, setPosts] = useState<HistoryPost[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    api.postHistory().then(setPosts).finally(() => setLoading(false))
  }, [])

  const syncMetrics = async () => {
    if (syncing || posts.length === 0) return
    const bizId = (posts[0] as any).business_id
    if (!bizId) return
    setSyncing(true)
    try {
      await api.syncMetrics(bizId)
      const updated = await api.postHistory()
      setPosts(updated)
    } catch { /* ignore */ }
    finally { setSyncing(false) }
  }

  const totalLikes = posts.reduce((s, p) => s + ((p as any).likes || 0), 0)
  const totalComments = posts.reduce((s, p) => s + ((p as any).comments || 0), 0)
  const totalReach = posts.reduce((s, p) => s + ((p as any).reach || 0), 0)
  const avgEngagement = posts.length > 0
    ? (posts.reduce((s, p) => s + ((p as any).engagement_rate || 0), 0) / posts.length).toFixed(1)
    : '0.0'

  return (
    <div>
      {/* Metrics summary */}
      {posts.length > 0 && (
        <div className="row mb-3">
          <div className="col-6 col-lg-3">
            <div className="info-box mb-2" style={{ borderRadius: 10 }}>
              <span className="info-box-icon bg-danger" style={{ borderRadius: '10px 0 0 10px' }}><i className="fas fa-heart" /></span>
              <div className="info-box-content">
                <span className="info-box-text">Total Likes</span>
                <span className="info-box-number">{totalLikes.toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div className="col-6 col-lg-3">
            <div className="info-box mb-2" style={{ borderRadius: 10 }}>
              <span className="info-box-icon bg-primary" style={{ borderRadius: '10px 0 0 10px' }}><i className="fas fa-comment" /></span>
              <div className="info-box-content">
                <span className="info-box-text">Total Comments</span>
                <span className="info-box-number">{totalComments.toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div className="col-6 col-lg-3">
            <div className="info-box mb-2" style={{ borderRadius: 10 }}>
              <span className="info-box-icon bg-info" style={{ borderRadius: '10px 0 0 10px' }}><i className="fas fa-eye" /></span>
              <div className="info-box-content">
                <span className="info-box-text">Alcance Total</span>
                <span className="info-box-number">{totalReach.toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div className="col-6 col-lg-3">
            <div className="info-box mb-2" style={{ borderRadius: 10 }}>
              <span className="info-box-icon bg-success" style={{ borderRadius: '10px 0 0 10px' }}><i className="fas fa-chart-line" /></span>
              <div className="info-box-content">
                <span className="info-box-text">Engajamento Medio</span>
                <span className="info-box-number">{avgEngagement}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center p-4"><i className="fas fa-spinner fa-spin fa-2x" /></div>
      ) : posts.length === 0 ? (
        <div className="card">
          <div className="card-body text-center text-muted py-5">
            <i className="fas fa-history fa-3x mb-3 d-block" />
            <p>Nenhum post publicado ainda.</p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h3 className="card-title"><i className="fas fa-history mr-2" />Posts Publicados</h3>
            <button className="btn btn-sm btn-outline-primary" onClick={syncMetrics} disabled={syncing}>
              {syncing ? <span className="spinner-border spinner-border-sm" /> : <><i className="fas fa-sync mr-1" />Atualizar metricas</>}
            </button>
          </div>
          <div className="card-body p-0">
            <table className="table table-striped mb-0">
              <thead>
                <tr>
                  <th>Imagem</th>
                  <th>Business</th>
                  <th>Formato</th>
                  <th>Caption</th>
                  <th style={{ textAlign: 'center' }}><i className="fas fa-heart text-danger" /></th>
                  <th style={{ textAlign: 'center' }}><i className="fas fa-comment text-primary" /></th>
                  <th style={{ textAlign: 'center' }}><i className="fas fa-eye text-info" /></th>
                  <th style={{ textAlign: 'center' }}>Eng%</th>
                  <th>Publicado</th>
                </tr>
              </thead>
              <tbody>
                {posts.map(p => {
                  const likes = (p as any).likes || 0
                  const comments = (p as any).comments || 0
                  const reach = (p as any).reach || 0
                  const eng = (p as any).engagement_rate || 0
                  return (
                    <tr key={p.id}>
                      <td>
                        {p.image_url && (
                          <img src={imgSrc(p.image_url)} alt="" style={{ width: 50, height: 50, objectFit: 'cover', borderRadius: 6 }} />
                        )}
                      </td>
                      <td className="small">{p.business_name}</td>
                      <td><span className="badge badge-primary">{p.format}</span></td>
                      <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                        {p.caption}
                      </td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>{likes > 0 ? likes : '—'}</td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>{comments > 0 ? comments : '—'}</td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>{reach > 0 ? reach.toLocaleString() : '—'}</td>
                      <td style={{ textAlign: 'center' }}>
                        {eng > 0 ? (
                          <span className={`badge badge-${eng >= 5 ? 'success' : eng >= 2 ? 'warning' : 'secondary'}`}>
                            {eng}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="small">{p.posted_at ? new Date(p.posted_at).toLocaleDateString('pt-BR') : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
