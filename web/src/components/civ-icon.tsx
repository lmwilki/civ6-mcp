"use client";

import Image from "next/image";
import { getCivSymbol } from "@/lib/civ-registry";

interface CivIconProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
  size?: "sm" | "md";
}

const sizes = {
  sm: { circle: "h-5 w-5", icon: "h-3 w-3" },
  md: { circle: "h-6 w-6", icon: "h-3 w-3" },
};

export function CivIcon({ icon: Icon, color, size = "md" }: CivIconProps) {
  const s = sizes[size];
  return (
    <div
      className={`flex ${s.circle} shrink-0 items-center justify-center rounded-full`}
      style={{ backgroundColor: color, opacity: 0.75 }}
    >
      <Icon className={`${s.icon} text-white`} />
    </div>
  );
}

/** Renders a civ's symbol image, or null if unavailable */
export function CivSymbol({
  civ,
  className = "h-3.5 w-3.5",
}: {
  civ: string;
  className?: string;
}) {
  const sym = getCivSymbol(civ);
  if (!sym) return null;
  return (
    <Image
      src={sym}
      alt=""
      width={14}
      height={14}
      className={`${className} shrink-0 rounded-full object-cover`}
    />
  );
}
