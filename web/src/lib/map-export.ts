import { Rectangle, type Application } from "pixi.js";

export interface ExportOptions {
  app: Application;
  renderTurn: (turn: number) => void;
  initialTurn: number;
  maxTurn: number;
  onProgress: (pct: number) => void;
  signal?: AbortSignal;
  /** Crop region in CSS pixels (excludes cylindrical wrap copies) */
  cropRegion?: { x: number; y: number; w: number; h: number };
}

/** Compute FPS to target ~30 second clip */
function targetFps(totalTurns: number): number {
  return Math.max(4, Math.min(30, Math.ceil(totalTurns / 30)));
}

/** Extract a single-map-width canvas, cropping out the 3x cylindrical copies */
function extractFrame(app: Application, crop?: ExportOptions["cropRegion"]): HTMLCanvasElement {
  if (crop) {
    return app.renderer.extract.canvas({
      target: app.stage,
      resolution: 1,
      frame: new Rectangle(crop.x, crop.y, crop.w, crop.h),
    }) as HTMLCanvasElement;
  }
  return app.renderer.extract.canvas({
    target: app.stage,
    resolution: 1,
  }) as HTMLCanvasElement;
}

// ── PNG (single frame) ──────────────────────────────────────────────────────

export async function exportPng(
  app: Application,
  crop?: ExportOptions["cropRegion"],
): Promise<Blob> {
  app.render();
  const canvas = extractFrame(app, crop);
  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))),
      "image/png",
    );
  });
}

// ── Video (WebM via MediaRecorder) ──────────────────────────────────────────

export async function exportVideo(opts: ExportOptions): Promise<Blob> {
  const { app, renderTurn, initialTurn, maxTurn, onProgress, signal, cropRegion } = opts;
  const totalFrames = maxTurn - initialTurn + 1;
  const fps = targetFps(totalFrames);
  const frameDuration = 1000 / fps;

  // If cropping, render to an offscreen canvas and stream from that
  const cropW = cropRegion ? cropRegion.w : Math.round(app.screen.width);
  const cropH = cropRegion ? cropRegion.h : Math.round(app.screen.height);

  const offscreen = document.createElement("canvas");
  offscreen.width = cropW;
  offscreen.height = cropH;
  const offCtx = offscreen.getContext("2d")!;

  const stream = offscreen.captureStream(0);
  const videoTrack = stream.getVideoTracks()[0];

  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
    ? "video/webm;codecs=vp9"
    : "video/webm;codecs=vp8";

  const recorder = new MediaRecorder(stream, {
    mimeType,
    videoBitsPerSecond: 4_000_000,
  });

  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };

  const done = new Promise<Blob>((resolve) => {
    recorder.onstop = () =>
      resolve(new Blob(chunks, { type: mimeType }));
  });

  recorder.start();

  for (let turn = initialTurn; turn <= maxTurn; turn++) {
    if (signal?.aborted) break;

    renderTurn(turn);
    app.render();

    const frame = extractFrame(app, cropRegion);
    offCtx.clearRect(0, 0, cropW, cropH);
    offCtx.drawImage(frame, 0, 0);

    if ("requestFrame" in videoTrack) {
      (videoTrack as unknown as { requestFrame: () => void }).requestFrame();
    }

    onProgress((turn - initialTurn + 1) / totalFrames);
    await new Promise((r) => setTimeout(r, Math.max(1, frameDuration / 4)));
  }

  await new Promise((r) => setTimeout(r, 200));
  recorder.stop();
  return done;
}

// ── GIF (via modern-gif) ────────────────────────────────────────────────────

export async function exportGif(opts: ExportOptions): Promise<Blob> {
  const { app, renderTurn, initialTurn, maxTurn, onProgress, signal, cropRegion } = opts;
  const { Encoder } = await import("modern-gif");

  const totalFrames = maxTurn - initialTurn + 1;
  const fps = targetFps(totalFrames);
  const delay = Math.round(1000 / fps);

  const width = cropRegion ? cropRegion.w : Math.round(app.screen.width);
  const height = cropRegion ? cropRegion.h : Math.round(app.screen.height);

  const encoder = new Encoder({ width, height, maxColors: 256 });

  for (let turn = initialTurn; turn <= maxTurn; turn++) {
    if (signal?.aborted) break;

    renderTurn(turn);
    app.render();

    const frame = extractFrame(app, cropRegion);
    await encoder.encode({ data: frame, delay });

    onProgress((turn - initialTurn + 1) / totalFrames);

    if ((turn - initialTurn) % 3 === 0) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  return encoder.flush("blob");
}
