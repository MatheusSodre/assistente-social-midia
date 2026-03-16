import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { HistoryPost } from '../services/api'

export function HistoryPage() {
  const [posts, setPosts] = useState<HistoryPost[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.postHistory().then(setPosts).finally(() => setLoading(false))
  }, [])

  return (
    <div>
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
          <div className="card-body p-0">
            <table className="table table-striped mb-0">
              <thead>
                <tr>
                  <th>Imagem</th>
                  <th>Business</th>
                  <th>Formato</th>
                  <th>Caption</th>
                  <th>Publicado em</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {posts.map(p => (
                  <tr key={p.id}>
                    <td>
                      {p.image_url && (
                        <img
                          src={p.image_url.startsWith('/') ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${p.image_url}` : p.image_url}
                          alt=""
                          style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 4 }}
                        />
                      )}
                    </td>
                    <td>{p.business_name}</td>
                    <td><span className="badge badge-primary">{p.format}</span></td>
                    <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.caption}
                    </td>
                    <td>{p.posted_at ? new Date(p.posted_at).toLocaleString('pt-BR') : '—'}</td>
                    <td>
                      <span className={`badge badge-${p.status === 'published' ? 'success' : p.status === 'failed' ? 'danger' : 'warning'}`}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
