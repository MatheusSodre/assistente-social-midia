import { useEffect, useRef, useState } from "react";
import { BriefingForm } from "@/components/marketing/BriefingForm";
import { ExportButtons } from "@/components/marketing/ExportButtons";
import { GenerationProgress } from "@/components/marketing/GenerationProgress";
import {
  KonvaComposer,
  type KonvaComposerHandle,
} from "@/components/marketing/KonvaComposer";
import { PreviewCard } from "@/components/marketing/PreviewCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBrandMemoryList } from "@/hooks/useBrandMemory";
import { useGeneration, type Generation } from "@/hooks/useGeneration";
import { useGenerationStream } from "@/hooks/useSSE";
import { useTemplates } from "@/hooks/useTemplates";

export default function CreatePost() {
  const { create, creating, fetchOne, fetchAssetUrl } = useGeneration();
  const { items: brands } = useBrandMemoryList();
  const { items: templates } = useTemplates();
  const [generation, setGeneration] = useState<Generation | null>(null);
  const { status, error: streamError, closed } = useGenerationStream(
    generation?.id ?? null,
  );
  const [signedBgUrl, setSignedBgUrl] = useState<string | null>(null);
  const composerRef = useRef<KonvaComposerHandle>(null);

  // quando termina, recarrega a generation completa pra pegar result
  useEffect(() => {
    if (!generation || !closed || status !== "done") return;
    void (async () => {
      const fresh = await fetchOne(generation.id);
      setGeneration(fresh);
      try {
        const { url } = await fetchAssetUrl(generation.id, "image_png");
        setSignedBgUrl(url);
      } catch {
        /* sem signed URL ainda */
      }
    })();
  }, [closed, status, generation, fetchOne, fetchAssetUrl]);

  async function handleSubmit(brief: string, templateId: string | null) {
    setGeneration(null);
    setSignedBgUrl(null);
    const gen = await create(brief, templateId);
    setGeneration(gen);
  }

  const brand = brands[0];
  const template =
    (generation?.template_id &&
      templates.find((t) => t.id === generation.template_id)) ||
    templates[0];

  const inProgress = !!generation && !["done", "failed"].includes(status ?? "");
  const done = status === "done" && generation?.result.caption;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Criar Post</h1>
        <p className="text-sm text-muted-foreground">
          Briefing curto → conteúdo completo em ~30s a 1min.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <BriefingForm onSubmit={handleSubmit} loading={creating || inProgress} />

        <Card>
          <CardHeader>
            <CardTitle>Progresso</CardTitle>
          </CardHeader>
          <CardContent>
            {!generation && (
              <p className="text-sm text-muted-foreground">
                Envie um briefing para começar.
              </p>
            )}
            {generation && (
              <GenerationProgress status={status} error={streamError} />
            )}
          </CardContent>
        </Card>
      </div>

      {done && generation && template && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center">
              <KonvaComposer
                ref={composerRef}
                width={template.dimensions.width}
                height={template.dimensions.height}
                backgroundUrl={signedBgUrl}
                headline={generation.result.headline ?? ""}
                logoUrl={brand?.visual_identity.logo_url ?? null}
                primaryColor={brand?.visual_identity.primary_color ?? "#FFFFFF"}
              />
            </CardContent>
          </Card>
          <div className="space-y-4">
            <PreviewCard generation={generation} />
            <ExportButtons generation={generation} composerRef={composerRef} />
          </div>
        </div>
      )}
    </div>
  );
}
