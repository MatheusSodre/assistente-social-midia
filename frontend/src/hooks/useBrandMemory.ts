import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api-client";

export interface Persona {
  name: string;
  role?: string | null;
  pains: string[];
  goals: string[];
}

export interface ToneOfVoice {
  style?: string | null;
  do: string[];
  dont: string[];
  examples: string[];
}

export interface VisualIdentity {
  primary_color?: string | null;
  secondary_color?: string | null;
  fonts: string[];
  logo_url?: string | null;
  style_description?: string | null;
}

export interface Competitor {
  name: string;
  handle?: string | null;
  notes?: string | null;
}

export interface Example {
  caption?: string | null;
  image_url?: string | null;
  why_it_works?: string | null;
}

export interface BrandMemory {
  id: string;
  tenant_id: string;
  name: string;
  positioning: string | null;
  icp: Persona[];
  tone_of_voice: ToneOfVoice;
  visual_identity: VisualIdentity;
  pillars: string[];
  competitors: Competitor[];
  examples: Example[];
  created_at: string;
  updated_at: string;
}

export type BrandMemoryPayload = Omit<
  BrandMemory,
  "id" | "tenant_id" | "created_at" | "updated_at"
>;

export function emptyPayload(): BrandMemoryPayload {
  return {
    name: "",
    positioning: "",
    icp: [],
    tone_of_voice: { style: "", do: [], dont: [], examples: [] },
    visual_identity: {
      primary_color: "#FF6B2B",
      secondary_color: "#080808",
      fonts: [],
      logo_url: "",
      style_description: "",
    },
    pillars: [],
    competitors: [],
    examples: [],
  };
}

export function useBrandMemoryList() {
  const [items, setItems] = useState<BrandMemory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<BrandMemory[]>("/api/v1/brand-memory");
      setItems(data);
    } catch (e: unknown) {
      setError(extractError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { items, loading, error, reload };
}

export const brandMemoryApi = {
  create: (payload: BrandMemoryPayload) =>
    api.post<BrandMemory>("/api/v1/brand-memory", payload),
  update: (id: string, payload: Partial<BrandMemoryPayload>) =>
    api.patch<BrandMemory>(`/api/v1/brand-memory/${id}`, payload),
  remove: (id: string) =>
    api.delete<void>(`/api/v1/brand-memory/${id}`),
};

function extractError(e: unknown): string {
  if (e && typeof e === "object" && "detail" in e) {
    return String((e as { detail: unknown }).detail);
  }
  return e instanceof Error ? e.message : String(e);
}
