import { useCallback, useState } from "react";
import { api } from "@/lib/api-client";

export type GenerationStatus =
  | "pending"
  | "brand_loading"
  | "content_generating"
  | "image_generating"
  | "validating"
  | "done"
  | "failed";

export interface GenerationResult {
  caption: string | null;
  hashtags: string[];
  headline: string | null;
  visual_brief: string | null;
  background_path: string | null;
  background_url: string | null;
  brand_review:
    | {
        approved: boolean;
        reason: string;
        suggestions: string[];
      }
    | null;
  error: string | null;
}

export interface Generation {
  id: string;
  tenant_id: string;
  brief: string;
  template_id: string | null;
  status: GenerationStatus;
  result: GenerationResult;
  cost_cents: number;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface AssetUrl {
  url: string;
  expires_in: number;
}

export function useGeneration() {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(
    async (brief: string, templateId: string | null) => {
      setCreating(true);
      setError(null);
      try {
        const gen = await api.post<Generation>("/api/v1/generations", {
          brief,
          template_id: templateId,
        });
        return gen;
      } catch (e: unknown) {
        const msg =
          e && typeof e === "object" && "detail" in e
            ? String((e as { detail: unknown }).detail)
            : String(e);
        setError(msg);
        throw e;
      } finally {
        setCreating(false);
      }
    },
    [],
  );

  const fetchOne = useCallback(
    (id: string) => api.get<Generation>(`/api/v1/generations/${id}`),
    [],
  );

  const fetchAssetUrl = useCallback(
    (id: string, type: "image_png" | "carousel_zip" | "copy_text") =>
      api.get<AssetUrl>(`/api/v1/assets/${id}/${type}`),
    [],
  );

  return { create, creating, error, fetchOne, fetchAssetUrl };
}
