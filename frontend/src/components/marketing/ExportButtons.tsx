import { Copy, Download, FileText } from "lucide-react";
import { useState, type RefObject } from "react";
import { Button } from "@/components/ui/button";
import type { Generation } from "@/hooks/useGeneration";
import { useGeneration } from "@/hooks/useGeneration";
import type { KonvaComposerHandle } from "./KonvaComposer";

interface Props {
  generation: Generation;
  composerRef: RefObject<KonvaComposerHandle | null>;
}

export function ExportButtons({ generation, composerRef }: Props) {
  const { fetchAssetUrl } = useGeneration();
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  async function copyCaption() {
    const text =
      [generation.result.caption, generation.result.hashtags.join(" ")]
        .filter(Boolean)
        .join("\n\n");
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function downloadPng() {
    const url = composerRef.current?.toPngDataUrl();
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `orbitaia-${generation.id.slice(0, 8)}.png`;
    a.click();
  }

  async function downloadCopyTxt() {
    setBusy("txt");
    try {
      const { url } = await fetchAssetUrl(generation.id, "copy_text");
      window.open(url, "_blank");
    } catch {
      // se asset não foi gerado ainda no backend, gera localmente
      const text =
        [generation.result.caption, generation.result.hashtags.join(" ")]
          .filter(Boolean)
          .join("\n\n");
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `orbitaia-${generation.id.slice(0, 8)}.txt`;
      a.click();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => void copyCaption()} variant="outline">
        <Copy className="mr-1 h-4 w-4" />
        {copied ? "Copiado!" : "Copiar caption"}
      </Button>
      <Button onClick={downloadPng} variant="outline">
        <Download className="mr-1 h-4 w-4" />
        PNG
      </Button>
      <Button
        onClick={() => void downloadCopyTxt()}
        variant="outline"
        disabled={busy === "txt"}
      >
        <FileText className="mr-1 h-4 w-4" />
        Copy .txt
      </Button>
    </div>
  );
}
