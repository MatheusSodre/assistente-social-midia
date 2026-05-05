import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

export default function Dashboard() {
  const [items, setItems] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Generation[]>("/api/v1/generations?limit=5")
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  const totalCost = items.reduce((sum, g) => sum + g.cost_cents, 0);
  const byStatus = items.reduce<Record<string, number>>((acc, g) => {
    acc[g.status] = (acc[g.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Últimas gerações e métricas.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Gerações (últimas 5)</CardDescription>
            <CardTitle className="text-3xl">{loading ? "…" : items.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Custo dessas 5</CardDescription>
            <CardTitle className="text-3xl">
              ${(totalCost / 100).toFixed(2)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Concluídas</CardDescription>
            <CardTitle className="text-3xl">{byStatus.done ?? 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Últimas gerações</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {loading && <p className="text-sm text-muted-foreground">Carregando...</p>}
          {!loading && items.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Nada ainda. <Link to="/criar" className="text-primary hover:underline">Crie o primeiro post</Link>.
            </p>
          )}
          {items.map((g) => (
            <Link
              key={g.id}
              to={`/historico`}
              className="flex items-center justify-between rounded-md border border-border p-3 text-sm hover:bg-accent/10"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate">{g.brief}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {new Date(g.created_at).toLocaleString("pt-BR")} · ${(g.cost_cents / 100).toFixed(2)}
                </div>
              </div>
              <span className="ml-3 shrink-0 rounded-full bg-secondary px-2 py-0.5 text-xs">
                {STATUS_LABEL[g.status] ?? g.status}
              </span>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
