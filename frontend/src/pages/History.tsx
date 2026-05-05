import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api-client";
import type { Generation } from "@/hooks/useGeneration";

const STATUS_LABEL: Record<string, string> = {
  pending: "Pendente",
  brand_loading: "Carregando marca",
  content_generating: "Gerando copy",
  image_generating: "Gerando imagem",
  validating: "Validando",
  done: "Pronto",
  failed: "Falhou",
};

export default function History() {
  const [items, setItems] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api
      .get<Generation[]>("/api/v1/generations?limit=200")
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  const filtered =
    filter === "all" ? items : items.filter((g) => g.status === filter);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Histórico</h1>
        <p className="text-sm text-muted-foreground">
          {items.length} gerações no total.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {["all", "done", "failed", "image_generating", "content_generating"].map(
          (s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`rounded-full px-3 py-1 text-xs transition-colors ${
                filter === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/70"
              }`}
            >
              {s === "all" ? "Todos" : STATUS_LABEL[s] ?? s}
            </button>
          ),
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Lista</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {loading && <p className="text-sm text-muted-foreground">Carregando...</p>}
          {!loading && filtered.length === 0 && (
            <p className="text-sm text-muted-foreground">Nenhum item.</p>
          )}
          {filtered.map((g) => (
            <details
              key={g.id}
              className="rounded-md border border-border p-3 text-sm"
            >
              <summary className="flex cursor-pointer items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">
                    {g.result.headline ?? g.brief.slice(0, 80)}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {new Date(g.created_at).toLocaleString("pt-BR")} · ${(g.cost_cents / 100).toFixed(2)}
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-secondary px-2 py-0.5 text-xs">
                  {STATUS_LABEL[g.status] ?? g.status}
                </span>
              </summary>
              <div className="mt-3 space-y-2">
                <div className="text-xs uppercase text-muted-foreground">Brief</div>
                <div className="whitespace-pre-wrap text-sm">{g.brief}</div>
                {g.result.caption && (
                  <>
                    <div className="text-xs uppercase text-muted-foreground">
                      Caption
                    </div>
                    <div className="whitespace-pre-wrap text-sm">
                      {g.result.caption}
                    </div>
                  </>
                )}
                {g.result.error && (
                  <div className="rounded-md bg-destructive/10 p-2 text-xs text-destructive">
                    {g.result.error}
                  </div>
                )}
              </div>
            </details>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
