import { Sparkles } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useTemplates } from "@/hooks/useTemplates";

interface Props {
  onSubmit: (brief: string, templateId: string | null) => void;
  loading?: boolean;
}

export function BriefingForm({ onSubmit, loading }: Props) {
  const { items, loading: loadingTpl } = useTemplates();
  const [brief, setBrief] = useState("");
  const [templateId, setTemplateId] = useState<string | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Briefing</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="brief">Sobre o que é o post?</Label>
          <Textarea
            id="brief"
            rows={6}
            placeholder="Ex: Anúncio do nosso novo serviço de geração de carrosseis em IA. Tom motivador para empreendedores cansados de criar conteúdo manualmente."
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Template</Label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {loadingTpl && (
              <span className="text-sm text-muted-foreground">
                Carregando...
              </span>
            )}
            {!loadingTpl && (
              <button
                type="button"
                onClick={() => setTemplateId(null)}
                className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                  templateId === null
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border hover:bg-accent/10"
                }`}
              >
                Auto (primeiro)
              </button>
            )}
            {items.map((t) => (
              <button
                type="button"
                key={t.id}
                onClick={() => setTemplateId(t.id)}
                className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                  templateId === t.id
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border hover:bg-accent/10"
                }`}
              >
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-muted-foreground">
                  {t.dimensions.width}×{t.dimensions.height} · {t.type}
                </div>
              </button>
            ))}
          </div>
        </div>

        <Button
          onClick={() => onSubmit(brief.trim(), templateId)}
          disabled={loading || !brief.trim()}
          className="w-full"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          {loading ? "Gerando..." : "Gerar conteúdo"}
        </Button>
      </CardContent>
    </Card>
  );
}
