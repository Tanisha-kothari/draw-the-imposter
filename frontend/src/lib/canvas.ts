export interface Point { x: number; y: number; pressure?: number; }

export function getCanvasPoint(
  canvas: HTMLCanvasElement,
  clientX: number,
  clientY: number
): Point {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY,
  };
}

export function setupCanvas(canvas: HTMLCanvasElement, width: number, height: number) {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext('2d')!;
  ctx.scale(dpr, dpr);
  return ctx;
}

export function drawStroke(
  ctx: CanvasRenderingContext2D,
  stroke: { tool: string; color: string; size: number; points: Point[] }
) {
  if (stroke.points.length < 2) return;
  
  ctx.beginPath();
  ctx.strokeStyle = stroke.tool === 'eraser' ? '#1f2937' : stroke.color;
  ctx.lineWidth = stroke.size;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
  for (let i = 1; i < stroke.points.length; i++) {
    ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
  }
  ctx.stroke();
}

export function clearCanvas(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.fillStyle = '#1f2937';
  ctx.fillRect(0, 0, width, height);
}
