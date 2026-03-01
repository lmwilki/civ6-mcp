import type { Application } from "pixi.js";

export interface ExportOptions {
  app: Application;
  renderTurn: (turn: number) => void;
  initialTurn: number;
  maxTurn: number;
  onProgress: (pct: number) => void;
}

/** Compute FPS to target ~30 second clip */
function targetFps(totalTurns: number): number {
  return Math.max(4, Math.min(30, Math.ceil(totalTurns / 30)));
}

// ── PNG (single frame) ──────────────────────────────────────────────────────

export async function exportPng(app: Application): Promise<Blob> {
  app.render();
  const canvas = app.renderer.extract.canvas({
    target: app.stage,
    resolution: 1,
  }) as HTMLCanvasElement;
  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))),
      "image/png",
    );
  });
}

// ── Video (WebM via MediaRecorder) ──────────────────────────────────────────

export async function exportVideo(opts: ExportOptions): Promise<Blob> {
  const { app, renderTurn, initialTurn, maxTurn, onProgress } = opts;
  const totalFrames = maxTurn - initialTurn + 1;
  const fps = targetFps(totalFrames);
  const frameDuration = 1000 / fps;

  const canvas = app.canvas as HTMLCanvasElement;
  const stream = canvas.captureStream(0);
  const videoTrack = stream.getVideoTracks()[0];

  // Pick best supported codec
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
    renderTurn(turn);
    app.render();

    // Signal new frame
    if ("requestFrame" in videoTrack) {
      (videoTrack as unknown as { requestFrame: () => void }).requestFrame();
    }

    onProgress((turn - initialTurn + 1) / totalFrames);

    // Pace frames — MediaRecorder uses real-time timing
    await new Promise((r) => setTimeout(r, Math.max(1, frameDuration / 4)));
  }

  // Hold last frame briefly
  await new Promise((r) => setTimeout(r, 200));
  recorder.stop();
  return done;
}

// ── GIF (via modern-gif) ────────────────────────────────────────────────────

export async function exportGif(opts: ExportOptions): Promise<Blob> {
  const { app, renderTurn, initialTurn, maxTurn, onProgress } = opts;
  const { Encoder } = await import("modern-gif");

  const totalFrames = maxTurn - initialTurn + 1;
  const fps = targetFps(totalFrames);
  const delay = Math.round(1000 / fps);

  // Use CSS pixel dimensions (not DPR-scaled) for reasonable file size
  const width = Math.round(app.screen.width);
  const height = Math.round(app.screen.height);

  const encoder = new Encoder({ width, height, maxColors: 256 });

  for (let turn = initialTurn; turn <= maxTurn; turn++) {
    renderTurn(turn);
    app.render();

    const extractedCanvas = app.renderer.extract.canvas({
      target: app.stage,
      resolution: 1,
    }) as HTMLCanvasElement;

    await encoder.encode({ data: extractedCanvas, delay });

    onProgress((turn - initialTurn + 1) / totalFrames);

    // Yield to main thread periodically
    if ((turn - initialTurn) % 3 === 0) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  return encoder.flush("blob");
}
