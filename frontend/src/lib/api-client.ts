import { AUTH_BYPASS, supabase } from "./supabase";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3002";

async function getAuthHeader(): Promise<Record<string, string>> {
  if (AUTH_BYPASS || !supabase) return {};
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

export interface ApiError {
  status: number;
  detail: string;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const auth = await getAuthHeader();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...auth,
    ...((init.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw { status: res.status, detail } satisfies ApiError;
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
};

export const sseUrl = (path: string) => `${API_URL}${path}`;
