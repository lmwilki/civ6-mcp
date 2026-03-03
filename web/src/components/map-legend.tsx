import type { MapDataDoc } from "@/lib/diary-types";
import { cleanCivName } from "@/lib/diary-types";
import { canonicalCivName, getDefaultLeader } from "@/lib/civ-registry";
import { CivSymbol } from "./civ-icon";

interface MapLegendProps {
  players: MapDataDoc["players"];
  playerColors: Map<number, { primary: string; secondary: string }>;
}

export function MapLegend({ players, playerColors }: MapLegendProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {players
        .filter((p) => !p.csType)
        .map((p) => {
          const civName = canonicalCivName(cleanCivName(p.civ));
          const leader = getDefaultLeader(civName);
          return (
            <div
              key={p.pid}
              className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
            >
              <CivSymbol civ={civName} className="h-3 w-3" />
              <span className="text-xs font-medium text-marble-600">
                {civName}
              </span>
              {leader && (
                <span className="text-xs text-marble-400">{leader}</span>
              )}
            </div>
          );
        })}

      {/* City-states */}
      {players.some((p) => p.csType) && (
        <>
          <span className="self-center text-xs text-marble-400">|</span>
          {players
            .filter((p) => p.csType)
            .map((p) => {
              const colors = playerColors.get(p.pid);
              return (
                <div
                  key={p.pid}
                  className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
                >
                  <span
                    className="inline-block h-2 w-2 rotate-45"
                    style={{
                      backgroundColor: "#1a1a2e",
                      border: `1.5px solid ${colors?.secondary ?? "#888"}`,
                    }}
                  />
                  <span className="text-xs font-medium text-marble-400">
                    {canonicalCivName(cleanCivName(p.civ))}
                  </span>
                </div>
              );
            })}
        </>
      )}
    </div>
  );
}
