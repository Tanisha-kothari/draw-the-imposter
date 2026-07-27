import { useEffect, useRef } from 'react';
import type { CanvasStroke } from '../../types';

interface CanvasViewerProps {
  imageData?: string;
  strokes?: CanvasStroke[];
  width?: number;
  height?: number;
  playerNumber?: number;
  showPlayerLabel?: boolean;
  combinedStrokes?: CanvasStroke[]; // all strokes for shared canvas (in order)
}

export default function CanvasViewer({
  imageData,
  strokes,
  width = 300,
  height = 200,
  playerNumber,
  showPlayerLabel = false,
  combinedStrokes,
}: CanvasViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const renderStrokesOnCanvas = (ctx: CanvasRenderingContext2D, s: CanvasStroke[], w: number, h: number) => {
    s.forEach((stroke) => {
      if (stroke.points.length < 2) return;
      ctx.beginPath();
      ctx.strokeStyle = stroke.tool === 'eraser' ? '#1f2937' : stroke.color;
      ctx.lineWidth = stroke.size;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.moveTo(stroke.points[0].x * (w / 600), stroke.points[0].y * (h / 400));
      for (let i = 1; i < stroke.points.length; i++) {
        ctx.lineTo(stroke.points[i].x * (w / 600), stroke.points[i].y * (h / 400));
      }
      ctx.stroke();
    });
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d')!;
    ctx.scale(dpr, dpr);
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, width, height);

    // Prefer combinedStrokes (shared canvas) over imageData over individual strokes
    if (combinedStrokes && combinedStrokes.length > 0) {
      renderStrokesOnCanvas(ctx, combinedStrokes, width, height);
    } else if (imageData && imageData.length > 0) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, width, height);
      img.src = imageData;
    } else if (strokes && strokes.length > 0) {
      renderStrokesOnCanvas(ctx, strokes, width, height);
    }
  }, [imageData, strokes, combinedStrokes, width, height]);

  return (
    <div className="relative rounded-xl overflow-hidden border border-gray-700">
      <canvas ref={canvasRef} className="w-full" />
      {showPlayerLabel && playerNumber !== undefined && (
        <div className="absolute top-2 left-2 bg-gray-900/80 px-3 py-1 rounded-lg text-sm font-medium">
          Player {playerNumber + 1}
        </div>
      )}
    </div>
  );
}
