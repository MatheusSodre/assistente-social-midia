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
