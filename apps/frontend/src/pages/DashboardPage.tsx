import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { ContentDraft } from '../services/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function imgSrc(url?: string) {
  if (!url) return ''
  return url.startsWith('/') ? `${API_BASE}${url}` : url
}

function FormatBadge({ format }: { format: string }) {
  const map: Record<string, string> = { post: 'primary', story: 'success', reel: 'warning' }
  return (
    <span className={`badge badge-${map[format] ?? 'secondary'} mr-1`}>
      <i className={`fas fa-${format === 'story' ? 'image' : format === 'reel' ? 'film' : 'th'} mr-1`} />
      {format.toUpperCase()}
    </span>
  )
}

interface DraftModalProps {
  draft: ContentDraft
  actionLoading: string | null
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPublish: (id: string) => void
  onClose: () => void
}

function DraftModal({ draft, actionLoading, onApprove, onReject, onPublish, onClose }: DraftModalProps) {
  const busy = !!actionLoading

  return (
    <div
      className="modal fade show"
      style={{ display: 'block', background: 'rgba(0,0,0,0.6)', zIndex: 1050 }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="modal-dialog modal-dialog-scrollable" style={{ maxWidth: 480 }}>
        <div className="modal-content" style={{ borderRadius: 12, overflow: 'hidden' }}>

          {/* Header estilo Instagram */}
          <div className="modal-header py-2 px-3" style={{ borderBottom: '1px solid #efefef' }}>
            <div className="d-flex align-items-center" style={{ gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 16,
              }}>
                <i className="fab fa-instagram" />
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, lineHeight: 1.2 }}>{draft.business_name}</div>
                <div style={{ fontSize: 11, color: '#8e8e8e' }}>
                  <FormatBadge format={draft.format} />
                </div>
              </div>
            </div>
            <button type="button" className="close" style={{ marginLeft: 'auto' }} onClick={onClose}>&times;</button>
          </div>

          <div className="modal-body p-0" style={{ overflowY: 'auto', maxHeight: '75vh' }}>
            {/* Imagem quadrada */}
            {draft.image_url ? (
              <div style={{ width: '100%', aspectRatio: '1/1', background: '#000', overflow: 'hidden' }}>
                <img
                  src={imgSrc(draft.image_url)}
                  alt="Preview"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </div>
            ) : (
              <div className="d-flex align-items-center justify-content-center bg-light" style={{ aspectRatio: '1/1' }}>
                <span className="text-muted small text-center">
                  <i className="fas fa-image fa-2x d-block mb-1" />Sem imagem
                </span>
              </div>
            )}

            {/* Ações estilo Instagram */}
            <div className="px-3 pt-2 pb-1 d-flex" style={{ gap: 14, fontSize: 22 }}>
              <i className="far fa-heart" style={{ cursor: 'default', color: '#262626' }} />
              <i className="far fa-comment" style={{ cursor: 'default', color: '#262626' }} />
              <i className="far fa-paper-plane" style={{ cursor: 'default', color: '#262626' }} />
            </div>

            {/* Caption + hashtags */}
            <div className="px-3 pb-3">
              <p style={{ fontSize: 14, lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                <span style={{ fontWeight: 600, marginRight: 6 }}>{draft.business_name}</span>
                {draft.caption}
              </p>
              {draft.hashtags?.length > 0 && (
                <p style={{ fontSize: 13, color: '#00376b', marginTop: 4, marginBottom: 0 }}>
                  {draft.hashtags.map(h => `#${h}`).join(' ')}
                </p>
              )}
              {draft.best_posting_time && (
                <p style={{ fontSize: 11, color: '#8e8e8e', marginTop: 6, marginBottom: 0 }}>
                  <i className="fas fa-clock mr-1" />Melhor horário: {draft.best_posting_time}
                </p>
              )}
            </div>
          </div>

          <div className="modal-footer justify-content-between">
            <button className="btn btn-secondary btn-sm" onClick={onClose}>Fechar</button>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => onReject(draft.id)}
                disabled={busy}
              >
                {actionLoading === draft.id + '_reject'
                  ? <span className="spinner-border spinner-border-sm" />
                  : <><i className="fas fa-times mr-1" />Rejeitar</>}
              </button>
              <button
                className="btn btn-success btn-sm"
                onClick={() => onApprove(draft.id)}
                disabled={busy}
              >
                {actionLoading === draft.id
                  ? <span className="spinner-border spinner-border-sm" />
                  : <><i className="fas fa-check mr-1" />Aprovar</>}
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onPublish(draft.id)}
                disabled={busy}
              >
                {actionLoading === draft.id + '_publish'
                  ? <span className="spinner-border spinner-border-sm" />
                  : <><i className="fas fa-paper-plane mr-1" />Publicar agora</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const [pendingDrafts, setPendingDrafts] = useState<ContentDraft[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'danger' } | null>(null)
  const [selected, setSelected] = useState<ContentDraft | null>(null)

  const load = async () => {
    try {
      const drafts = await api.listDrafts('pending_approval')
      setPendingDrafts(drafts)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const showMsg = (text: string, type: 'success' | 'danger' = 'success') => {
    setMsg({ text, type })
    setTimeout(() => setMsg(null), 4000)
  }

  const handleApprove = async (id: string) => {
    setActionLoading(id)
    try {
      await api.approveDraft(id)
      showMsg('Conteúdo aprovado!')
      setSelected(null)
      load()
    } catch (e: any) {
      showMsg(`Erro: ${e.message}`, 'danger')
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async (id: string) => {
    setActionLoading(id + '_reject')
    try {
      await api.rejectDraft(id)
      showMsg('Conteúdo rejeitado.')
      setSelected(null)
      load()
    } catch (e: any) {
      showMsg(`Erro: ${e.message}`, 'danger')
    } finally {
      setActionLoading(null)
    }
  }

  const handlePublishNow = async (id: string) => {
    if (!confirm('Publicar agora no Instagram?')) return
    setActionLoading(id + '_publish')
    try {
      await api.approveDraft(id)
      await api.publishNow(id)
      showMsg('Publicado com sucesso no Instagram!')
      setSelected(null)
      load()
    } catch (e: any) {
      showMsg(`Erro ao publicar: ${e.message}`, 'danger')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div>
      {msg && (
        <div className={`alert alert-${msg.type} alert-dismissible`}>
          <i className={`fas fa-${msg.type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2`} />
          {msg.text}
          <button type="button" className="close" onClick={() => setMsg(null)}>&times;</button>
        </div>
      )}

      {loading ? (
        <div className="text-center p-5">
          <div className="spinner-border text-primary" />
          <p className="mt-2 text-muted small">Carregando...</p>
        </div>
      ) : pendingDrafts.length === 0 ? (
        <div className="card">
          <div className="card-body text-center text-muted py-5">
            <i className="fas fa-check-circle fa-3x mb-3 d-block text-success" />
            <h5>Tudo em dia!</h5>
            <p className="mb-0">Nenhum conteúdo aguardando aprovação.</p>
          </div>
        </div>
      ) : (
        <>
          <p className="text-muted mb-3 small">
            <i className="fas fa-info-circle mr-1" />
            {pendingDrafts.length} {pendingDrafts.length === 1 ? 'post aguardando' : 'posts aguardando'} aprovação.
            Clique em um card para ver o post completo.
          </p>
          <div className="row">
            {pendingDrafts.map(draft => (
              <div key={draft.id} className="col-md-6 col-lg-4 mb-4">
                <div
                  className="card h-100 shadow-sm"
                  style={{ cursor: 'pointer', transition: 'box-shadow 0.15s' }}
                  onClick={() => setSelected(draft)}
                  onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.15)')}
                  onMouseLeave={e => (e.currentTarget.style.boxShadow = '')}
                >
                  {/* Imagem */}
                  {draft.image_url ? (
                    <div style={{ position: 'relative', paddingTop: draft.format === 'story' ? '75%' : '56%', overflow: 'hidden', background: '#000' }}>
                      <img
                        src={imgSrc(draft.image_url)}
                        alt="Preview"
                        style={{
                          position: 'absolute', top: 0, left: 0,
                          width: '100%', height: '100%',
                          objectFit: 'cover',
                        }}
                      />
                      <div style={{
                        position: 'absolute', top: 8, left: 8,
                      }}>
                        <FormatBadge format={draft.format} />
                      </div>
                    </div>
                  ) : (
                    <div className="d-flex align-items-center justify-content-center bg-light" style={{ height: 160 }}>
                      <span className="text-muted small text-center">
                        <i className="fas fa-image fa-2x d-block mb-1" />
                        Sem imagem
                      </span>
                      <div style={{ position: 'absolute', top: 8, left: 8 }}>
                        <FormatBadge format={draft.format} />
                      </div>
                    </div>
                  )}

                  <div className="card-body pb-2">
                    <p className="font-weight-bold mb-1 small text-primary">{draft.business_name}</p>
                    {/* Caption truncada — apenas prévia */}
                    <p className="card-text text-dark mb-2" style={{ fontSize: 13, lineHeight: 1.5 }}>
                      {draft.caption.slice(0, 120)}{draft.caption.length > 120 ? (
                        <span className="text-primary"> ... ver mais</span>
                      ) : ''}
                    </p>
                    {/* Hashtags preview */}
                    {draft.hashtags?.length > 0 && (
                      <p className="text-muted mb-1" style={{ fontSize: 11 }}>
                        {draft.hashtags.slice(0, 4).map(h => `#${h}`).join(' ')}
                        {draft.hashtags.length > 4 && <span> +{draft.hashtags.length - 4}</span>}
                      </p>
                    )}
                    {draft.best_posting_time && (
                      <span className="text-muted" style={{ fontSize: 11 }}>
                        <i className="fas fa-clock mr-1" />{draft.best_posting_time}
                      </span>
                    )}
                  </div>

                  <div className="card-footer bg-transparent pt-0" style={{ display: 'flex', gap: 6 }}>
                    <button
                      className="btn btn-success btn-sm flex-fill"
                      onClick={e => { e.stopPropagation(); handleApprove(draft.id) }}
                      disabled={!!actionLoading}
                    >
                      {actionLoading === draft.id
                        ? <span className="spinner-border spinner-border-sm" />
                        : <><i className="fas fa-check mr-1" />Aprovar</>}
                    </button>
                    <button
                      className="btn btn-danger btn-sm flex-fill"
                      onClick={e => { e.stopPropagation(); handleReject(draft.id) }}
                      disabled={!!actionLoading}
                    >
                      {actionLoading === draft.id + '_reject'
                        ? <span className="spinner-border spinner-border-sm" />
                        : <><i className="fas fa-times mr-1" />Rejeitar</>}
                    </button>
                    <button
                      className="btn btn-outline-secondary btn-sm"
                      title="Ver post completo"
                      onClick={e => { e.stopPropagation(); setSelected(draft) }}
                    >
                      <i className="fas fa-expand-alt" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {selected && (
        <DraftModal
          draft={selected}
          actionLoading={actionLoading}
          onApprove={handleApprove}
          onReject={handleReject}
          onPublish={handlePublishNow}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
