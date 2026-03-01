import { Rectangle, type Application } from "pixi.js";

export interface ExportOptions {
  app: Application;
  renderTurn: (turn: number) => void;
  initialTurn: number;
  maxTurn: number;
  onProgress: (pct: number) => void;
  signal?: AbortSignal;
  /** Crop region in screen pixels (excludes cylindrical wrap copies) */
  cropRegion?: { x: number; y: number; w: number; h: number };
}

/** Compute FPS to target ~30 second clip */
function targetFps(totalTurns: number): number {
  return Math.max(4, Math.min(30, Math.ceil(totalTurns / 30)));
}

/** Extract a cropped frame at given resolution */
function extractFrame(
  app: Application,
  crop: ExportOptions["cropRegion"],
  resolution: number,
): HTMLCanvasElement {
  if (crop) {
    return app.renderer.extract.canvas({
      target: app.stage,
      resolution,
      frame: new Rectangle(crop.x, crop.y, crop.w, crop.h),
    }) as HTMLCanvasElement;
  }
  return app.renderer.extract.canvas({
    target: app.stage,
    resolution,
  }) as HTMLCanvasElement;
}

/** Read raw RGBA pixel data from a canvas */
function canvasToImageData(canvas: HTMLCanvasElement): ImageData {
  const ctx = canvas.getContext("2d", { willReadFrequently: true })!;
  return ctx.getImageData(0, 0, canvas.width, canvas.height);
}

// ── PNG (single frame, 2x resolution) ───────────────────────────────────────

export async function exportPng(
  app: Application,
  crop?: ExportOptions["cropRegion"],
): Promise<Blob> {
  app.render();
  const canvas = extractFrame(app, crop, 2);
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

  const cropW = cropRegion ? cropRegion.w : Math.round(app.screen.width);
  const cropH = cropRegion ? cropRegion.h : Math.round(app.screen.height);

  // Offscreen canvas that MediaRecorder streams from
  const offscreen = document.createElement("canvas");
  offscreen.width = cropW;
  offscreen.height = cropH;
  const offCtx = offscreen.getContext("2d")!;

  // Use fps-based capture — MediaRecorder samples at this rate
  const stream = offscreen.captureStream(fps);

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

  // Paint first frame before starting the timed loop
  renderTurn(initialTurn);
  app.render();
  const firstFrame = extractFrame(app, cropRegion, 1);
  offCtx.drawImage(firstFrame, 0, 0);

  // Wait one frame duration so MediaRecorder captures the first frame
  await new Promise((r) => setTimeout(r, frameDuration));

  for (let turn = initialTurn + 1; turn <= maxTurn; turn++) {
    if (signal?.aborted) break;

    renderTurn(turn);
    app.render();

    const frame = extractFrame(app, cropRegion, 1);
    offCtx.clearRect(0, 0, cropW, cropH);
    offCtx.drawImage(frame, 0, 0);

    onProgress((turn - initialTurn + 1) / totalFrames);

    // Hold frame for the target duration so MediaRecorder captures it
    await new Promise((r) => setTimeout(r, frameDuration));
  }

  // Hold last frame briefly
  await new Promise((r) => setTimeout(r, 300));
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

    // Extract at 1x and read raw RGBA pixels for accurate color reproduction
    const frame = extractFrame(app, cropRegion, 1);
    const imageData = canvasToImageData(frame);
    await encoder.encode({ data: imageData.data, delay });

    onProgress((turn - initialTurn + 1) / totalFrames);

    if ((turn - initialTurn) % 3 === 0) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  return encoder.flush("blob");
}
