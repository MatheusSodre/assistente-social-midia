import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTemplates } from "@/hooks/useTemplates";

export default function Templates() {
  const { items, loading } = useTemplates();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Templates</h1>
        <p className="text-sm text-muted-foreground">
          Layouts disponíveis para composição via Konva.
        </p>
      </div>

      {loading && <p className="text-sm text-muted-foreground">Carregando...</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((t) => {
          const previewW = 240;
          const ratio = t.dimensions.width / t.dimensions.height;
          const previewH = previewW / ratio;
          return (
            <Card key={t.id}>
              <CardHeader>
                <CardTitle className="text-base">{t.name}</CardTitle>
                <p className="text-xs text-muted-foreground">
                  {t.dimensions.width}×{t.dimensions.height} · {t.type}
                </p>
              </CardHeader>
              <CardContent>
                <div
                  className="relative rounded-md border border-border bg-secondary"
                  style={{ width: previewW, height: previewH }}
                >
                  <span className="absolute left-2 top-2 text-[10px] uppercase tracking-wide text-muted-foreground">
                    {t.type}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
