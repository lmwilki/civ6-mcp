import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
} from "lucide-react";
import { MapExportControls } from "./map-export-controls";

const SPEED_LABELS = ["1x", "2x", "5x", "10x"];

interface MapControlsProps {
  playing: boolean;
  exporting: string | null;
  exportProgress: number;
  exportMenuOpen: boolean;
  exportMenuRef: React.RefObject<HTMLDivElement | null>;
  currentTurn: number;
  initialTurn: number;
  maxTurn: number;
  speed: number;
  onPlay: () => void;
  onReset: () => void;
  onJumpEnd: () => void;
  onSeek: (turn: number) => void;
  onSpeedChange: () => void;
  onToggleExportMenu: () => void;
  onExport: (format: "png" | "video" | "gif") => void;
  onCancelExport: () => void;
}

export function MapControls({
  playing,
  exporting,
  exportProgress,
  exportMenuOpen,
  exportMenuRef,
  currentTurn,
  initialTurn,
  maxTurn,
  speed,
  onPlay,
  onReset,
  onJumpEnd,
  onSeek,
  onSpeedChange,
  onToggleExportMenu,
  onExport,
  onCancelExport,
}: MapControlsProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onReset}
        disabled={!!exporting}
        className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
        title="Reset to start"
      >
        <SkipBack className="h-4 w-4" />
      </button>

      <button
        onClick={onPlay}
        disabled={!!exporting}
        className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
        title={playing ? "Pause" : "Play"}
      >
        {playing ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4" />
        )}
      </button>

      <button
        onClick={onJumpEnd}
        disabled={!!exporting}
        className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
        title="Jump to end"
      >
        <SkipForward className="h-4 w-4" />
      </button>

      <input
        type="range"
        min={initialTurn}
        max={maxTurn}
        value={currentTurn}
        disabled={!!exporting}
        aria-label="Turn navigation"
        onChange={(e) => onSeek(Number(e.target.value))}
        className="flex-1 accent-gold-dark disabled:opacity-30"
      />

      <button
        onClick={onSpeedChange}
        disabled={!!exporting}
        className="rounded border border-marble-300 px-2 py-0.5 font-mono text-xs tabular-nums text-marble-600 hover:bg-marble-200 disabled:opacity-30 disabled:pointer-events-none"
        title="Change speed"
      >
        {SPEED_LABELS[speed]}
      </button>

      <MapExportControls
        exporting={exporting}
        exportProgress={exportProgress}
        exportMenuOpen={exportMenuOpen}
        exportMenuRef={exportMenuRef}
        onToggleMenu={onToggleExportMenu}
        onExport={onExport}
        onCancel={onCancelExport}
      />
    </div>
  );
}
