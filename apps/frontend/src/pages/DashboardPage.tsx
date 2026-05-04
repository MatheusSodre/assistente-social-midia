import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api'
import type { ContentDraft } from '../services/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function imgSrc(url?: string) {
  if (!url) return ''
  return url.startsWith('/') ? `${API_BASE}${url}` : url
}

function FormatBadge({ format }: { format: string }) {
  const map: Record<string, string> = { post: 'primary', story: 'success', reel: 'warning', carrossel: 'info' }
  const iconMap: Record<string, string> = { post: 'th', story: 'image', reel: 'film', carrossel: 'images' }
  return (
    <span className={`badge badge-${map[format] ?? 'secondary'} mr-1`}>
      <i className={`fas fa-${iconMap[format] ?? 'th'} mr-1`} />
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

function CarouselViewer({ urls, imgSrcFn }: { urls: string[]; imgSrcFn: (url?: string) => string }) {
  const [idx, setIdx] = useState(0)
  const prev = useCallback(() => setIdx(i => Math.max(0, i - 1)), [])
  const next = useCallback(() => setIdx(i => Math.min(urls.length - 1, i + 1)), [urls.length])

  return (
    <div style={{ width: '100%', background: '#fafafa', position: 'relative' }}>
      <img
        src={imgSrcFn(urls[idx])}
        alt={`Slide ${idx + 1}`}
        style={{ width: '100%', maxHeight: 375, objectFit: 'contain', display: 'block' }}
      />
      {/* Arrows */}
      {idx > 0 && (
        <button onClick={prev} style={{
          position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)',
          background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', borderRadius: '50%',
          width: 32, height: 32, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <i className="fas fa-chevron-left" />
        </button>
      )}
      {idx < urls.length - 1 && (
        <button onClick={next} style={{
          position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
          background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', borderRadius: '50%',
          width: 32, height: 32, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <i className="fas fa-chevron-right" />
        </button>
      )}
      {/* Dots */}
      <div style={{
        position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: 5,
      }}>
        {urls.map((_, i) => (
          <div key={i} style={{
            width: 6, height: 6, borderRadius: '50%',
            background: i === idx ? '#0095f6' : 'rgba(255,255,255,0.7)',
            cursor: 'pointer',
          }} onClick={() => setIdx(i)} />
        ))}
      </div>
      {/* Counter */}
      <div style={{
        position: 'absolute', top: 8, right: 8, background: 'rgba(0,0,0,0.6)',
        color: '#fff', borderRadius: 12, padding: '2px 8px', fontSize: 12,
      }}>
        {idx + 1}/{urls.length}
      </div>
    </div>
  )
}

function DraftModal({ draft, actionLoading, onApprove, onReject, onPublish, onClose }: DraftModalProps) {
  const busy = !!actionLoading
  const isStory = draft.format === 'story' || draft.format === 'reel'
  const isCarousel = draft.format === 'carrossel' && draft.image_urls && draft.image_urls.length > 0

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1050,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{ display: 'flex', gap: 24, maxHeight: '90vh', maxWidth: 920 }}>

        {/* Phone Mockup — cores forçadas para evitar dark mode */}
        <div style={{
          width: 375, minWidth: 375, background: '#ffffff', color: '#262626',
          borderRadius: 40, border: '6px solid #1a1a1a', overflow: 'hidden',
          display: 'flex', flexDirection: 'column', maxHeight: '85vh',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}>
          {/* Notch */}
          <div style={{ background: '#1a1a1a', height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <div style={{ width: 80, height: 20, background: '#000', borderRadius: 10 }} />
          </div>

          {/* Instagram Header */}
          <div style={{ padding: '8px 12px', borderBottom: '1px solid #efefef', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0, background: '#fff' }}>
            <span style={{ fontWeight: 700, fontSize: 18, fontFamily: 'cursive', color: '#262626' }}>Instagram</span>
            <div style={{ display: 'flex', gap: 16, fontSize: 18, color: '#262626' }}>
              <i className="far fa-heart" />
              <i className="far fa-paper-plane" />
            </div>
          </div>

          {/* Post Content — scrollable */}
          <div style={{ flex: 1, overflowY: 'auto', background: '#fff' }}>
            {/* Profile row */}
            <div style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0,
              }}>
                {(draft.business_name || 'B')[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, color: '#262626' }}>{draft.business_name}</div>
                <div style={{ fontSize: 10, color: '#8e8e8e' }}>Patrocinado</div>
              </div>
              <div style={{ marginLeft: 'auto', fontSize: 16, color: '#262626' }}>...</div>
            </div>

            {/* Image / Carousel */}
            {isCarousel ? (
              <CarouselViewer urls={draft.image_urls!} imgSrcFn={imgSrc} />
            ) : draft.image_url ? (
              <div style={{ width: '100%', background: '#fafafa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <img
                  src={imgSrc(draft.image_url)}
                  alt="Preview"
                  style={{ width: '100%', maxHeight: isStory ? 500 : 375, objectFit: 'contain', display: 'block' }}
                />
              </div>
            ) : (
              <div style={{ width: '100%', height: 300, background: '#fafafa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: '#c7c7c7', fontSize: 14 }}><i className="fas fa-image fa-2x" /></span>
              </div>
            )}

            {/* Action icons */}
            <div style={{ padding: '10px 12px 4px', display: 'flex', gap: 14, fontSize: 22, background: '#fff' }}>
              <i className="far fa-heart" style={{ color: '#262626' }} />
              <i className="far fa-comment" style={{ color: '#262626', transform: 'scaleX(-1)' }} />
              <i className="far fa-paper-plane" style={{ color: '#262626' }} />
              <i className="far fa-bookmark" style={{ color: '#262626', marginLeft: 'auto' }} />
            </div>

            {/* Caption — cores forçadas escuras */}
            <div style={{ padding: '0 12px 12px', background: '#fff' }}>
              <p style={{ fontSize: 13, lineHeight: 1.5, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#262626' }}>
                <span style={{ fontWeight: 600, marginRight: 5, color: '#262626' }}>{draft.business_name?.toLowerCase().replace(/\s+/g, '')}</span>
                {draft.caption}
              </p>
              {draft.hashtags?.length > 0 && (
                <p style={{ fontSize: 13, color: '#00376b', marginTop: 4, marginBottom: 0 }}>
                  {draft.hashtags.map(h => `#${h}`).join(' ')}
                </p>
              )}
              <p style={{ fontSize: 10, color: '#8e8e8e', marginTop: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                2 horas atrás
              </p>
            </div>
          </div>

          {/* Bottom bar */}
          <div style={{ height: 4, background: '#1a1a1a', margin: '0 auto 8px', width: 120, borderRadius: 2, flexShrink: 0 }} />
        </div>

        {/* Side Panel — Actions + Metadata */}
        <div style={{
          width: 300, background: 'var(--bg-card)', borderRadius: 16, padding: 24,
          display: 'flex', flexDirection: 'column', gap: 16,
          boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
          overflowY: 'auto', color: 'var(--text-primary)',
        }}>
          <div>
            <h5 style={{ fontWeight: 700, fontSize: 16, marginBottom: 4, color: 'var(--text-primary)' }}>Preview do Post</h5>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: 0 }}>
              Veja como ficará no Instagram antes de aprovar
            </p>
          </div>

          {/* Metadata */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="d-flex align-items-center" style={{ gap: 8 }}>
              <FormatBadge format={draft.format} />
              <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{draft.business_name}</span>
            </div>
            {draft.best_posting_time && (
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                <i className="fas fa-clock mr-2" style={{ color: 'var(--text-muted)' }} />
                Melhor horário: <strong>{draft.best_posting_time}</strong>
              </div>
            )}
            {draft.call_to_action && (
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                <i className="fas fa-bullhorn mr-2" style={{ color: 'var(--text-muted)' }} />
                CTA: {draft.call_to_action}
              </div>
            )}
            {draft.visual_description && (
              <details style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                <summary style={{ cursor: 'pointer' }}>Prompt da imagem</summary>
                <p style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{draft.visual_description}</p>
              </details>
            )}
          </div>

          <hr style={{ margin: '4px 0' }} />

          {/* Action Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 'auto' }}>
            <button
              className="btn btn-success btn-lg btn-block"
              style={{ borderRadius: 10, fontWeight: 600, fontSize: 15 }}
              onClick={() => onApprove(draft.id)}
              disabled={busy}
            >
              {actionLoading === draft.id
                ? <span className="spinner-border spinner-border-sm" />
                : <><i className="fas fa-check mr-2" />Aprovar</>}
            </button>
            <button
              className="btn btn-primary btn-block"
              style={{ borderRadius: 10, fontWeight: 600, fontSize: 14 }}
              onClick={() => onPublish(draft.id)}
              disabled={busy}
            >
              {actionLoading === draft.id + '_publish'
                ? <span className="spinner-border spinner-border-sm" />
                : <><i className="fas fa-paper-plane mr-2" />Publicar agora</>}
            </button>
            <button
              className="btn btn-outline-danger btn-block"
              style={{ borderRadius: 10, fontSize: 14 }}
              onClick={() => onReject(draft.id)}
              disabled={busy}
            >
              {actionLoading === draft.id + '_reject'
                ? <span className="spinner-border spinner-border-sm" />
                : <><i className="fas fa-times mr-2" />Rejeitar</>}
            </button>
            <button
              className="btn btn-outline-secondary btn-block"
              style={{ borderRadius: 10, fontSize: 13 }}
              onClick={onClose}
            >
              Fechar
            </button>
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
                  {/* Imagem — contain para ver completa */}
                  {(draft.format === 'carrossel' && draft.image_urls?.length) ? (
                    <div style={{ position: 'relative', paddingTop: '100%', overflow: 'hidden', background: 'var(--bg-surface)' }}>
                      <img
                        src={imgSrc(draft.image_urls[0])}
                        alt="Preview"
                        style={{
                          position: 'absolute', top: 0, left: 0,
                          width: '100%', height: '100%',
                          objectFit: 'contain',
                        }}
                      />
                      <div style={{ position: 'absolute', top: 8, left: 8 }}>
                        <FormatBadge format={draft.format} />
                      </div>
                      <div style={{
                        position: 'absolute', top: 8, right: 8,
                        background: 'rgba(0,0,0,0.6)', color: '#fff', borderRadius: 8,
                        padding: '2px 8px', fontSize: 11, fontWeight: 600,
                      }}>
                        <i className="fas fa-images mr-1" />{draft.image_urls.length} slides
                      </div>
                    </div>
                  ) : draft.image_url ? (
                    <div style={{ position: 'relative', paddingTop: '100%', overflow: 'hidden', background: 'var(--bg-surface)' }}>
                      <img
                        src={imgSrc(draft.image_url)}
                        alt="Preview"
                        style={{
                          position: 'absolute', top: 0, left: 0,
                          width: '100%', height: '100%',
                          objectFit: 'contain',
                        }}
                      />
                      <div style={{ position: 'absolute', top: 8, left: 8 }}>
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
                    <p className="font-weight-bold mb-1 small" style={{ color: '#6f42c1' }}>{draft.business_name}</p>
                    <p className="card-text mb-2" style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text-primary)' }}>
                      {draft.caption.slice(0, 120)}{draft.caption.length > 120 ? (
                        <span style={{ color: '#6f42c1' }}> ... ver mais</span>
                      ) : ''}
                    </p>
                    {draft.hashtags?.length > 0 && (
                      <p className="mb-1" style={{ fontSize: 11, color: 'var(--text-hashtag)' }}>
                        {draft.hashtags.slice(0, 4).map(h => `#${h}`).join(' ')}
                        {draft.hashtags.length > 4 && <span> +{draft.hashtags.length - 4}</span>}
                      </p>
                    )}
                    {draft.best_posting_time && (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
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
