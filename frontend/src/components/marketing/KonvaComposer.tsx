import Konva from "konva";
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Image as KImage, Layer, Stage, Text } from "react-konva";

interface Props {
  width: number;
  height: number;
  backgroundUrl: string | null;
  headline: string;
  logoUrl?: string | null;
  primaryColor?: string | null;
}

export interface KonvaComposerHandle {
  toPngDataUrl: () => string | null;
}

function useImage(url: string | null) {
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!url) {
      setImg(null);
      return;
    }
    const i = new window.Image();
    i.crossOrigin = "anonymous";
    i.onload = () => setImg(i);
    i.onerror = () => setImg(null);
    i.src = url;
  }, [url]);
  return img;
}

export const KonvaComposer = forwardRef<KonvaComposerHandle, Props>(
  function KonvaComposer(
    { width, height, backgroundUrl, headline, logoUrl, primaryColor },
    ref,
  ) {
    const stageRef = useRef<Konva.Stage>(null);
    const bg = useImage(backgroundUrl);
    const logo = useImage(logoUrl ?? null);

    useImperativeHandle(ref, () => ({
      toPngDataUrl() {
        return stageRef.current?.toDataURL({ pixelRatio: 1 }) ?? null;
      },
    }));

    // escala visual: cabe em 540 de largura no preview, mantendo aspecto
    const previewWidth = 540;
    const scale = previewWidth / width;
    const previewHeight = height * scale;

    return (
      <div
        className="overflow-hidden rounded-lg border border-border bg-background"
        style={{ width: previewWidth, height: previewHeight }}
      >
        <Stage
          ref={stageRef}
          width={width}
          height={height}
          scaleX={scale}
          scaleY={scale}
          style={{ width: previewWidth, height: previewHeight }}
        >
          <Layer>
            {bg && (
              <KImage image={bg} width={width} height={height} listening={false} />
            )}
            {/* Overlay sutil pra texto ficar legível */}
            {bg && headline && (
              <KImage
                image={undefined}
                width={width}
                height={height}
                listening={false}
              />
            )}
            {headline && (
              <Text
                x={80}
                y={Math.max(80, height / 2 - 100)}
                width={width - 160}
                text={headline}
                fontSize={Math.round(width / 16)}
                fontFamily="Inter"
                fontStyle="700"
                fill={primaryColor ?? "#FFFFFF"}
                shadowColor="#000000"
                shadowBlur={20}
                shadowOpacity={0.6}
                align="left"
              />
            )}
            {logo && (
              <KImage
                image={logo}
                x={width - 200}
                y={height - 200}
                width={140}
                height={140}
                listening={false}
              />
            )}
          </Layer>
        </Stage>
      </div>
    );
  },
);
