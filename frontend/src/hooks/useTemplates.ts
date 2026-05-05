import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";

export interface Template {
  id: string;
  name: string;
  type: "post" | "carousel_slide" | "story";
  dimensions: { width: number; height: number };
  slots: Record<string, unknown>;
  layout_config: Record<string, unknown>;
}

export function useTemplates() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Template[]>("/api/v1/templates")
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  return { items, loading };
}
