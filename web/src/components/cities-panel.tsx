"use client";

import type { CityRow } from "@/lib/diary-types";
import { CollapsiblePanel } from "./collapsible-panel";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { Building2 } from "lucide-react";

interface CitiesPanelProps {
  cities: CityRow[];
}

export function CitiesPanel({ cities }: CitiesPanelProps) {
  if (cities.length === 0) return null;

  return (
    <CollapsiblePanel
      icon={<CivIcon icon={Building2} color={CIV6_COLORS.growth} size="sm" />}
      title={`Cities (${cities.length})`}
      defaultOpen
    >
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-marble-500">
              <th className="py-1 px-1 text-left">City</th>
              <th className="py-1 px-1 text-right">Pop</th>
              <th className="py-1 px-1 text-right">Food</th>
              <th className="py-1 px-1 text-right">Prod</th>
              <th className="py-1 px-1 text-right">Gold</th>
              <th className="py-1 px-1 text-right">Sci</th>
              <th className="py-1 px-1 text-right">Cul</th>
              <th className="py-1 px-1 text-right">Housing</th>
              <th className="py-1 px-1 text-right">Amenity</th>
              <th className="py-1 px-1 text-left">Producing</th>
              <th className="py-1 px-1 text-right">Loyalty</th>
            </tr>
          </thead>
          <tbody>
            {cities.map((c) => {
              const amenitySurplus = c.amenities - c.amenities_needed;
              return (
                <tr key={c.city_id} className="border-t border-marble-200/50">
                  <td className="py-1 px-1 font-medium text-marble-700">
                    {c.city}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.pop}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.food}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.production}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.gold}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.science}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.culture}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {c.housing}
                  </td>
                  <td
                    className={`py-1 px-1 text-right font-mono tabular-nums ${amenitySurplus < 0 ? "text-terracotta" : "text-marble-700"}`}
                  >
                    {amenitySurplus >= 0 ? "+" : ""}
                    {amenitySurplus}
                  </td>
                  <td className="py-1 px-1 font-mono text-marble-600">
                    {c.producing !== "NONE"
                      ? c.producing.replace(
                          /^(UNIT_|BUILDING_|DISTRICT_|PROJECT_)/,
                          "",
                        )
                      : "—"}
                  </td>
                  <td
                    className={`py-1 px-1 text-right font-mono tabular-nums ${c.loyalty < 50 ? "text-terracotta font-semibold" : "text-marble-700"}`}
                  >
                    {Math.round(c.loyalty)}
                    {c.loyalty_per_turn !== 0 && (
                      <span
                        className={`ml-0.5 text-[10px] ${c.loyalty_per_turn > 0 ? "text-patina" : "text-terracotta"}`}
                      >
                        {c.loyalty_per_turn > 0 ? "+" : ""}
                        {c.loyalty_per_turn.toFixed(1)}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </CollapsiblePanel>
  );
}
