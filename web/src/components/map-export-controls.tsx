import { X, Download, Camera, Film, ImageIcon } from "lucide-react";

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export { triggerDownload };

interface MapExportControlsProps {
  exporting: string | null;
  exportProgress: number;
  exportMenuOpen: boolean;
  exportMenuRef: React.RefObject<HTMLDivElement | null>;
  onToggleMenu: () => void;
  onExport: (format: "png" | "video" | "gif") => void;
  onCancel: () => void;
}

export function MapExportControls({
  exporting,
  exportProgress,
  exportMenuOpen,
  exportMenuRef,
  onToggleMenu,
  onExport,
  onCancel,
}: MapExportControlsProps) {
  if (exporting) {
    return (
      <div className="flex items-center gap-2 rounded border border-marble-300 px-2 py-1">
        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-marble-200">
          <div
            className="h-full rounded-full bg-gold-dark transition-all"
            style={{ width: `${exportProgress * 100}%` }}
          />
        </div>
        <span className="font-mono text-xs tabular-nums text-marble-500">
          {Math.round(exportProgress * 100)}%
        </span>
        <button
          onClick={onCancel}
          className="rounded p-0.5 text-marble-400 hover:bg-marble-200 hover:text-marble-700"
          title="Cancel export"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={exportMenuRef}>
      <button
        onClick={onToggleMenu}
        className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
        title="Export map"
      >
        <Download className="h-4 w-4" />
      </button>
      {exportMenuOpen && (
        <div className="absolute bottom-full right-0 mb-1 rounded border border-marble-300 bg-white shadow-md z-50">
          <button
            onClick={() => onExport("png")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <Camera className="h-3 w-3" /> Screenshot (PNG)
          </button>
          <button
            onClick={() => onExport("video")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <Film className="h-3 w-3" /> Export Video
          </button>
          <button
            onClick={() => onExport("gif")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <ImageIcon className="h-3 w-3" /> Export GIF
          </button>
        </div>
      )}
    </div>
  );
}
