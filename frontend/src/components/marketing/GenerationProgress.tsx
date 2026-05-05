import { Check, Circle, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS: { key: string; label: string }[] = [
  { key: "brand_loading", label: "Carregando marca" },
  { key: "content_generating", label: "Gerando copy" },
  { key: "image_generating", label: "Gerando imagem" },
  { key: "validating", label: "Validando branding" },
];

const ORDER = ["pending", ...STEPS.map((s) => s.key), "done"];

interface Props {
  status: string | null;
  error?: string | null;
}

export function GenerationProgress({ status, error }: Props) {
  const currentIdx = ORDER.indexOf(status ?? "pending");
  const failed = status === "failed";

  return (
    <ol className="space-y-3">
      {STEPS.map((step) => {
        const stepIdx = ORDER.indexOf(step.key);
        const done = currentIdx > stepIdx;
        const active = currentIdx === stepIdx;
        return (
          <li key={step.key} className="flex items-center gap-3">
            <span
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full",
                done && "bg-primary text-primary-foreground",
                active && "bg-primary/20 text-primary",
                !done && !active && "bg-muted text-muted-foreground",
                failed && active && "bg-destructive text-destructive-foreground",
              )}
            >
              {failed && active ? (
                <X className="h-4 w-4" />
              ) : done ? (
                <Check className="h-4 w-4" />
              ) : active ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Circle className="h-3 w-3" />
              )}
            </span>
            <span
              className={cn(
                "text-sm",
                active && "font-medium text-foreground",
                !active && "text-muted-foreground",
              )}
            >
              {step.label}
            </span>
          </li>
        );
      })}
      {failed && error && (
        <li className="text-sm text-destructive">Erro: {error}</li>
      )}
    </ol>
  );
}
