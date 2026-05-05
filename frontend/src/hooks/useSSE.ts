import { useEffect, useState } from "react";
import { sseUrl } from "@/lib/api-client";

export function useGenerationStream(generationId: string | null) {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [closed, setClosed] = useState(false);

  useEffect(() => {
    if (!generationId) return;
    setStatus(null);
    setError(null);
    setClosed(false);

    const url = sseUrl(`/api/v1/generations/${generationId}/stream`);
    const es = new EventSource(url);

    es.addEventListener("status", (evt) => {
      try {
        const data = JSON.parse((evt as MessageEvent).data) as {
          status?: string;
          error?: string;
        };
        if (data.status) setStatus(data.status);
        if (data.error) setError(data.error);
        if (data.status === "done" || data.status === "failed") {
          es.close();
          setClosed(true);
        }
      } catch {
        /* ignore */
      }
    });

    es.onerror = () => {
      // Backend fecha após terminal — onerror dispara nesse caso. OK.
      if (!closed) {
        // mas se fechou antes mesmo de status terminal, registra
      }
    };

    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generationId]);

  return { status, error, closed };
}
