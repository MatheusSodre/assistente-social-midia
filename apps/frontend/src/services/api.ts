export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

// Helpers para chamadas autenticadas
// Uso: const res = await get('/api/meu-modulo', authHeader())
export async function get(path: string, headers: Record<string, string> = {}) {
  const res = await fetch(`${API_BASE}${path}`, { headers })
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

export async function post(
  path: string,
  body: unknown,
  headers: Record<string, string> = {},
) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

export async function postForm(
  path: string,
  form: FormData,
  headers: Record<string, string> = {},
) {
  // SEM Content-Type — browser define o boundary
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: form,
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

export async function del(path: string, headers: Record<string, string> = {}) {
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers })
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`)
  return res.json()
}

// ─── Assistente Social Midia API ─────────────────────────────────────────────

function getToken(): string | null {
  return localStorage.getItem('aa_jwt')
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000) // 2 min timeout

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }))
      throw new Error(err.detail || err.error || `HTTP ${res.status}`)
    }
    return res.json()
  } catch (e: any) {
    if (e.name === 'AbortError') {
      throw new Error('A requisição demorou demais. Tente novamente.')
    }
    throw e
  } finally {
    clearTimeout(timeout)
  }
}

export const api = {
  // Businesses
  listBusinesses: () => request<Business[]>('GET', '/api/v1/businesses'),
  getBusiness: (id: string) => request<Business>('GET', `/api/v1/businesses/${id}`),
  createBusiness: (data: Partial<Business>) =>
    request<{ id: string; name: string; type: string }>('POST', '/api/v1/businesses', data),
  updateBusiness: (id: string, data: Partial<Business>) =>
    request<{ message: string; updated_fields: string[] }>('PUT', `/api/v1/businesses/${id}`, data),
  deleteBusiness: (id: string) =>
    request<{ message: string }>('DELETE', `/api/v1/businesses/${id}`),
  getReadiness: (id: string) => request<ReadinessResponse>('GET', `/api/v1/businesses/${id}/readiness`),
  analyzeUrl: (id: string, url: string) =>
    request<{ extracted: Record<string, unknown>; readiness: ReadinessResponse }>('POST', `/api/v1/businesses/${id}/analyze-url`, { url }),
  uploadDocument: async (businessId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    const token = localStorage.getItem('aa_jwt')
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(`${API_BASE}/api/v1/businesses/${businessId}/upload-document`, { method: 'POST', headers, body: form })
    if (!res.ok) { const err = await res.json().catch(() => ({ error: res.statusText })); throw new Error(err.detail || err.error || `HTTP ${res.status}`) }
    return res.json() as Promise<{ extracted: Record<string, unknown>; readiness: ReadinessResponse }>
  },
  connectInstagram: (businessId: string, data: { instagram_account_id: string; access_token: string }) =>
    request('POST', `/api/v1/businesses/${businessId}/connect-instagram`, data),

  // Content
  generateContent: (data: GenerateRequest) => request<ContentDraft>('POST', '/api/v1/content/generate', data),
  listDrafts: (status?: string) => request<ContentDraft[]>('GET', `/api/v1/content${status ? `?status=${status}` : ''}`),
  previewDraft: (id: string) => request<ContentDraft>('GET', `/api/v1/content/${id}/preview`),
  approveDraft: (id: string) => request('POST', `/api/v1/content/${id}/approve`),
  rejectDraft: (id: string) => request('POST', `/api/v1/content/${id}/reject`),
  generateImage: (id: string) => request<{ draft_id: string; image_url: string }>('POST', `/api/v1/content/${id}/generate-image`),

  // Schedule
  calendar: (month?: number, year?: number) => {
    const params = new URLSearchParams()
    if (month) params.set('month', String(month))
    if (year) params.set('year', String(year))
    return request<ScheduledPost[]>('GET', `/api/v1/schedule/calendar?${params}`)
  },
  schedulePost: (data: { draft_id: string; scheduled_for: string }) =>
    request('POST', '/api/v1/schedule/post', data),
  publishNow: (draftId: string) => request('POST', `/api/v1/schedule/publish-now/${draftId}`),

  // Posts
  postHistory: () => request<HistoryPost[]>('GET', '/api/v1/posts/history'),
  postAnalytics: (businessId: string) =>
    request<PostAnalytics>('GET', `/api/v1/posts/analytics?business_id=${businessId}`),

  // Strategy
  getStrategy: (businessId: string) => request<BrandStrategy>('GET', `/api/v1/strategy/${businessId}`),
  updateStrategy: (businessId: string, data: Partial<BrandStrategy>) =>
    request<BrandStrategy>('PUT', `/api/v1/strategy/${businessId}`, data),

  // Batch content
  generateBatch: (data: BatchGenerateRequest) =>
    request<BatchGenerateResponse>('POST', '/api/v1/content/generate-batch', data),

  // Agent
  agentChat: (data: { business_id: string; message: string }) =>
    request<AgentChatResponse>('POST', '/api/v1/agent/chat', data),
  agentHistory: (businessId: string) =>
    request<AgentHistoryResponse>('GET', `/api/v1/agent/history/${businessId}`),
  agentClearHistory: (businessId: string) =>
    request('DELETE', `/api/v1/agent/history/${businessId}`),

  // Agency (Sofia)
  agencyChat: (data: { business_id: string; message: string }) =>
    request<AgencyChatResponse>('POST', '/api/v1/agency/chat', data),
  agencyHistory: (businessId: string) =>
    request<AgentHistoryResponse>('GET', `/api/v1/agency/history/${businessId}`),
  agencyClearHistory: (businessId: string) =>
    request('DELETE', `/api/v1/agency/history/${businessId}`),

  // Google Ads / Luna
  getAdsAccount: (businessId: string) =>
    request<AdsAccount>('GET', `/api/v1/ads/account/${businessId}`),
  connectAdsAccount: (data: AdsAccountConnect) =>
    request('POST', '/api/v1/ads/account/connect', data),
  disconnectAdsAccount: (businessId: string) =>
    request('DELETE', `/api/v1/ads/account/${businessId}`),
  lunaChat: (data: { business_id: string; message: string }) =>
    request<AgentChatResponse>('POST', '/api/v1/ads/chat', data),
  lunaHistory: (businessId: string) =>
    request<AgentHistoryResponse>('GET', `/api/v1/ads/history/${businessId}`),
  lunaClearHistory: (businessId: string) =>
    request('DELETE', `/api/v1/ads/history/${businessId}`),

  // Finance
  financeConnectToken: () =>
    request<{ connect_token: string }>('POST', '/api/v1/finance/connect-token'),
  financeCreateConnection: (data: { item_id: string; connector_name?: string }) =>
    request<FinanceConnection>('POST', '/api/v1/finance/connections', data),
  financeListConnections: () =>
    request<FinanceConnection[]>('GET', '/api/v1/finance/connections'),
  financeDeleteConnection: (id: string) =>
    request<{ message: string }>('DELETE', `/api/v1/finance/connections/${id}`),
  financeTransactions: (params?: { days?: number; tipo?: string; categoria?: string; busca?: string }) => {
    const qs = new URLSearchParams()
    if (params?.days) qs.set('days', String(params.days))
    if (params?.tipo) qs.set('tipo', params.tipo)
    if (params?.categoria) qs.set('categoria', params.categoria)
    if (params?.busca) qs.set('busca', params.busca)
    return request<FinanceTransaction[]>('GET', `/api/v1/finance/transactions?${qs}`)
  },
  financeSync: () =>
    request<{ synced: number; errors: string[] }>('POST', '/api/v1/finance/sync'),
  financeAnalysis: () =>
    request<FinanceAnalysis>('GET', '/api/v1/finance/analysis'),
  financeAlerts: (days_ahead?: number) =>
    request<FinanceAlert[]>('GET', `/api/v1/finance/alerts${days_ahead ? `?days_ahead=${days_ahead}` : ''}`),

  // Designer / Pixel
  designerChat: async (data: { business_id: string; message: string; image?: File }) => {
    const form = new FormData()
    form.append('business_id', data.business_id)
    form.append('message', data.message)
    if (data.image) form.append('image', data.image)
    const token = localStorage.getItem('aa_jwt')
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(`${API_BASE}/api/v1/designer/chat`, { method: 'POST', headers, body: form })
    if (!res.ok) { const err = await res.json().catch(() => ({ error: res.statusText })); throw new Error(err.detail || err.error || `HTTP ${res.status}`) }
    return res.json() as Promise<DesignerChatResponse>
  },
  getVisualIdentity: (businessId: string) =>
    request<VisualIdentity>('GET', `/api/v1/designer/identity/${businessId}`),
  updateVisualIdentity: (businessId: string, data: Partial<VisualIdentity>) =>
    request<{ success: boolean }>('PUT', `/api/v1/designer/identity/${businessId}`, data),
  designerClearHistory: (businessId: string) =>
    request('DELETE', `/api/v1/designer/history/${businessId}`),
}

// Types
export interface Business {
  id: string
  name: string
  type: string
  description?: string
  location?: string
  website_url?: string
  instagram_handle?: string
  linkedin_url?: string
  services?: string[] | string
  target_audience?: string
  differentials?: string
  instagram_account_id?: string
  brand_context?: Record<string, unknown>
  criado_em: string
}

export interface ReadinessResponse {
  score: number
  ready: boolean
  missing: Array<{ field: string; label: string; weight: number }>
  total_fields: number
  filled_fields: number
}

export interface ContentDraft {
  id: string
  business_id: string
  business_name?: string
  format: 'post' | 'story' | 'reel'
  caption: string
  hashtags: string[]
  image_url?: string
  visual_description?: string
  call_to_action?: string
  best_posting_time?: string
  status: 'pending_approval' | 'approved' | 'rejected' | 'published'
  scheduled_for?: string
  criado_em: string
}

export interface ScheduledPost {
  id: string
  content_draft_id: string
  platform: string
  scheduled_for: string
  posted_at?: string
  status: 'scheduled' | 'published' | 'failed'
  format: string
  caption: string
  image_url?: string
  business_name: string
}

export interface HistoryPost {
  id: string
  platform: string
  scheduled_for: string
  posted_at?: string
  instagram_media_id?: string
  status: string
  format: string
  caption: string
  image_url?: string
  business_name: string
}

export interface GenerateRequest {
  business_id: string
  objective: string
  format: 'post' | 'story' | 'reel'
  tone: 'profissional' | 'descontraido' | 'urgente' | 'educativo'
  audience: string
}

export interface BrandStrategy {
  id?: string
  business_id?: string
  personas?: Array<Record<string, unknown>>
  content_pillars?: string[]
  posting_frequency?: Record<string, unknown>
  brand_tone?: string
  brand_colors?: string[]
  competitors?: string[]
  goals?: string[]
}

export interface PostAnalytics {
  business_id: string
  total_drafts: number
  approved: number
  rejected: number
  published: number
  approval_rate_pct: number
  top_formats: Array<{ format: string; count: number }>
  best_times: Array<{ time: string; count: number }>
  trend_30d: Array<{ day: string; count: number }>
}

export interface BatchGenerateRequest {
  business_id: string
  items: Array<{
    objective: string
    format: 'post' | 'story' | 'reel'
    tone?: string
    audience?: string
  }>
}

export interface BatchGenerateResponse {
  created: number
  drafts: ContentDraft[]
  errors: Array<{ index: number; objective: string; error: string }>
}

export interface AgentChatResponse {
  response: string
  message_count: number
}

export interface AgencyChatResponse {
  response: string
  steps: Array<{ agent: string; action: string; status: string }>
  message_count: number
}

export interface AgentHistoryResponse {
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  business_id: string
}

export interface AdsAccount {
  connected: boolean
  business_id?: string
  customer_id?: string
  is_test_account?: boolean
  login_customer_id?: string
}

export interface AdsAccountConnect {
  business_id: string
  customer_id: string
  refresh_token: string
  login_customer_id?: string
  is_test_account: boolean
}

export interface DesignerChatResponse {
  response: string
  image_url?: string
  message_count: number
}

export interface FinanceConnection {
  id: string
  item_id: string
  connector_name?: string
  status: 'updating' | 'updated' | 'error'
  last_synced_at?: string
  created_at: string
}

export interface FinanceTransaction {
  id: string
  connection_id: string
  pluggy_id?: string
  account_id?: string
  date?: string
  description?: string
  amount?: number
  type?: 'CREDIT' | 'DEBIT'
  category?: string
  status: 'PENDING' | 'POSTED'
}

export interface FinanceAnalysis {
  summary: string
  top_categories: Array<{ category: string; total: number; count: number; percentage: number }>
  insights: string[]
  recommendations: string[]
}

export interface FinanceAlert {
  id: string
  description: string
  amount?: number
  date?: string
  days_until_due: number
  account_id?: string
}

export interface VisualIdentity {
  found?: boolean
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  background_color?: string
  text_color?: string
  font_heading?: string
  font_body?: string
  style_description?: string
  logo_url?: string
  extra_context?: string
}
