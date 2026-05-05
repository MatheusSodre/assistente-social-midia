import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Generation } from "@/hooks/useGeneration";

interface Props {
  generation: Generation;
}

export function PreviewCard({ generation }: Props) {
  const { result } = generation;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Resultado</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {result.headline && (
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Headline
            </div>
            <div className="mt-1 text-lg font-semibold">{result.headline}</div>
          </div>
        )}
        {result.caption && (
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Caption
            </div>
            <div className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">
              {result.caption}
            </div>
          </div>
        )}
        {result.hashtags.length > 0 && (
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Hashtags
            </div>
            <div className="mt-1 flex flex-wrap gap-2">
              {result.hashtags.map((h) => (
                <span
                  key={h}
                  className="rounded-full bg-secondary px-2 py-0.5 text-xs"
                >
                  {h}
                </span>
              ))}
            </div>
          </div>
        )}
        {result.brand_review && (
          <div className="rounded-md border border-border bg-card p-3 text-sm">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
              Brand review
              <span
                className={
                  result.brand_review.approved
                    ? "rounded-full bg-primary/15 px-2 py-0.5 text-primary"
                    : "rounded-full bg-destructive/15 px-2 py-0.5 text-destructive"
                }
              >
                {result.brand_review.approved ? "aprovado" : "reprovado"}
              </span>
            </div>
            <div className="mt-2">{result.brand_review.reason}</div>
            {result.brand_review.suggestions.length > 0 && (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                {result.brand_review.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
