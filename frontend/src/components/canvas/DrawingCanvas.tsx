import { useRef, useState, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import type { CanvasStroke } from '../../types';

const COLORS = ['#ffffff', '#000000', '#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];
const SIZES = [2, 4, 6, 8, 12];

export interface DrawingCanvasHandle {
  getImageData: () => string;
  getStrokes: () => CanvasStroke[];
  loadStrokes: (strokes: CanvasStroke[]) => void;
  clear: () => void;
  undo: () => void;
  setReadOnly: (readOnly: boolean) => void;
}

interface DrawingCanvasProps {
  readOnly?: boolean;
  width?: number;
  height?: number;
}

const CANVAS_LOG_PREFIX = '[CANVAS]';

const DrawingCanvas = forwardRef<DrawingCanvasHandle, DrawingCanvasProps>(({
  readOnly: initialReadOnly = false,
  width = 600,
  height = 400,
}, ref) => {
  const [tool, setTool] = useState<'pencil' | 'eraser'>('pencil');
  const [color, setColor] = useState('#ffffff');
  const [brushSize, setBrushSize] = useState(4);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const strokesRef = useRef<CanvasStroke[]>([]);
  const currentStrokeRef = useRef<CanvasStroke | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const initialStrokeCountRef = useRef(0);

  // Use refs instead of state for values read inside synchronous event handlers.
  // This avoids React 18 batching causing stale closures where mousemove fires
  // before the state update from mousedown is flushed.
  const isDrawingRef = useRef(false);
  const readOnlyRef = useRef(initialReadOnly);
  readOnlyRef.current = initialReadOnly;

  const drawStroke = (
    ctx: CanvasRenderingContext2D,
    stroke: CanvasStroke,
    w: number,
    h: number
  ) => {
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
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    console.log(`${CANVAS_LOG_PREFIX} Canvas initialized: ${width}x${height}`);

    const dpr = window.devicePixelRatio || 1;
    const prevWidth = canvas.width;
    const prevHeight = canvas.height;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    console.log(`${CANVAS_LOG_PREFIX} Context created, dpr=${dpr}, canvas pixels=${canvas.width}x${canvas.height}`);
    if (!ctx) {
      console.error(`${CANVAS_LOG_PREFIX} Failed to get 2D context`);
      return;
    }

    ctx.scale(dpr, dpr);
    ctxRef.current = ctx;

    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, width, height);

    if (strokesRef.current.length > 0) {
      console.log(`${CANVAS_LOG_PREFIX} Redrawing ${strokesRef.current.length} stored strokes`);
      strokesRef.current.forEach((s) => drawStroke(ctx, s, width, height));
    }
  }, [width, height]);

  const getCanvasPoint = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  };

  const startDrawing = useCallback((clientX: number, clientY: number, pressure?: number) => {
    if (readOnlyRef.current) return;
    isDrawingRef.current = true;
    const point = getCanvasPoint(clientX, clientY);
    console.log(`${CANVAS_LOG_PREFIX} Mouse down: (${point.x}, ${point.y})`);
    currentStrokeRef.current = {
      tool,
      color,
      size: brushSize,
      points: [{ ...point, pressure }],
    };
  }, [tool, color, brushSize]);

  const draw = useCallback((clientX: number, clientY: number, pressure?: number) => {
    if (!isDrawingRef.current || !currentStrokeRef.current || readOnlyRef.current) return;
    const point = getCanvasPoint(clientX, clientY);
    currentStrokeRef.current.points.push({ ...point, pressure });

    const ctx = ctxRef.current;
    if (!ctx || !canvasRef.current) return;

    const stroke = currentStrokeRef.current;
    const pts = stroke.points;
    if (pts.length < 2) return;

    const prev = pts[pts.length - 2];
    const curr = pts[pts.length - 1];
    console.log(`${CANVAS_LOG_PREFIX} Drawing line from (${prev.x}, ${prev.y}) to (${curr.x}, ${curr.y})`);

    ctx.beginPath();
    ctx.strokeStyle = stroke.tool === 'eraser' ? '#1f2937' : stroke.color;
    ctx.lineWidth = stroke.size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(curr.x, curr.y);
    ctx.stroke();
  }, []);

  const endDrawing = useCallback(() => {
    if (readOnlyRef.current || !currentStrokeRef.current) return;
    isDrawingRef.current = false;
    const completedStroke = currentStrokeRef.current;
    strokesRef.current.push(completedStroke);
    console.log(`${CANVAS_LOG_PREFIX} Stroke added: ${completedStroke.points.length} points`);
    currentStrokeRef.current = null;
  }, []);

  const clear = useCallback(() => {
    strokesRef.current = [];
    const ctx = ctxRef.current;
    if (!ctx || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, w, h);
  }, []);

  const undo = useCallback(() => {
    strokesRef.current.pop();
    const ctx = ctxRef.current;
    if (!ctx || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, w, h);
    strokesRef.current.forEach((s) => drawStroke(ctx, s, w, h));
  }, []);

  const getImageData = useCallback(() => {
    return canvasRef.current?.toDataURL('image/png') || '';
  }, []);

  const getStrokes = useCallback(() => [...strokesRef.current.slice(initialStrokeCountRef.current)], []);

  const loadStrokes = useCallback((strokes: CanvasStroke[]) => {
    strokesRef.current = [...strokes];
    initialStrokeCountRef.current = strokes.length;
    const ctx = ctxRef.current;
    if (!ctx || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, w, h);
    strokes.forEach((s) => drawStroke(ctx, s, w, h));
  }, []);

  const setReadOnlyFn = useCallback((r: boolean) => { readOnlyRef.current = r; }, []);

  useImperativeHandle(ref, () => ({ getImageData, getStrokes, loadStrokes, clear, undo, setReadOnly: setReadOnlyFn }), []);

  const handleMouseDown = (e: React.MouseEvent) => startDrawing(e.clientX, e.clientY);
  const handleMouseMove = (e: React.MouseEvent) => draw(e.clientX, e.clientY);
  const handleMouseUp = endDrawing;
  const handleMouseLeave = endDrawing;

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    startDrawing(touch.clientX, touch.clientY, (touch as any).force);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    draw(touch.clientX, touch.clientY, (touch as any).force);
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault();
    endDrawing();
  };

  return (
    <div ref={containerRef} className="flex flex-col items-center gap-4 w-full">
      {!readOnlyRef.current && (
        <div className="flex flex-wrap items-center gap-3 p-3 bg-gray-800 rounded-xl">
          <button
            onClick={() => setTool('pencil')}
            className={`p-2 rounded-lg transition-colors ${tool === 'pencil' ? 'bg-primary-600' : 'bg-gray-700 hover:bg-gray-600'}`}
            title="Pencil"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <button
            onClick={() => setTool('eraser')}
            className={`p-2 rounded-lg transition-colors ${tool === 'eraser' ? 'bg-primary-600' : 'bg-gray-700 hover:bg-gray-600'}`}
            title="Eraser"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          <div className="w-px h-8 bg-gray-600" />

          <div className="flex gap-1">
            {COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setColor(c)}
                className={`w-6 h-6 rounded-full border-2 transition-transform ${color === c ? 'border-white scale-125' : 'border-transparent'}`}
                style={{ backgroundColor: c }}
                title={c === '#ffffff' ? 'White' : 'Color'}
              />
            ))}
          </div>

          <div className="w-px h-8 bg-gray-600" />

          <div className="flex items-center gap-2">
            {SIZES.map((s) => (
              <button
                key={s}
                onClick={() => setBrushSize(s)}
                className={`rounded-full bg-gray-600 transition-all ${brushSize === s ? 'ring-2 ring-primary-500' : ''}`}
                style={{ width: s + 8, height: s + 8 }}
                title={`${s}px`}
              />
            ))}
          </div>

          <div className="w-px h-8 bg-gray-600" />

          <button
            onClick={undo}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
            title="Undo"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </button>
          <button
            onClick={clear}
            className="p-2 rounded-lg bg-red-600 hover:bg-red-700 transition-colors"
            title="Clear"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      )}

      <div className="relative rounded-2xl overflow-hidden shadow-2xl border-2 border-gray-700">
        <canvas
          ref={canvasRef}
          className="touch-none cursor-crosshair"
          width={width}
          height={height}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        />
      </div>
    </div>
  );
});

DrawingCanvas.displayName = 'DrawingCanvas';
export default DrawingCanvas;
