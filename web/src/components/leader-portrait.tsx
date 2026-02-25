import { getLeaderPortrait } from "@/lib/civ-images";
import { getModelMeta } from "@/lib/model-registry";

const SIZES = {
  sm: {
    portrait: "h-9 w-9",
    border: "border",
    badge: "h-4 w-4",
    badgeIcon: "h-2 w-2",
    offset: "-bottom-0.5 -right-0.5",
  },
  md: {
    portrait: "h-10 w-10",
    border: "border",
    badge: "h-4 w-4",
    badgeIcon: "h-2.5 w-2.5",
    offset: "-bottom-0.5 -right-0.5",
  },
  lg: {
    portrait: "h-14 w-14",
    border: "border-2",
    badge: "h-5 w-5",
    badgeIcon: "h-3 w-3",
    offset: "-bottom-0.5 -right-0.5",
  },
} as const;

interface LeaderPortraitProps {
  leader?: string | null;
  agentModel?: string | null;
  fallbackColor?: string;
  size?: keyof typeof SIZES;
}

export function LeaderPortrait({
  leader,
  agentModel,
  fallbackColor,
  size = "md",
}: LeaderPortraitProps) {
  const portrait = leader ? getLeaderPortrait(leader) : null;
  const modelMeta = agentModel ? getModelMeta(agentModel) : null;
  const s = SIZES[size];

  return (
    <div className="relative shrink-0">
      {portrait ? (
        <img
          src={portrait}
          alt={leader ?? ""}
          className={`${s.portrait} shrink-0 rounded-full ${s.border} border-marble-300 object-cover object-top`}
        />
      ) : (
        <span
          className={`inline-block ${s.portrait} shrink-0 rounded-full`}
          style={{ backgroundColor: fallbackColor ?? "#7A7269" }}
        />
      )}
      {modelMeta?.providerLogo && (
        <span
          className={`absolute ${s.offset} flex ${s.badge} items-center justify-center rounded-full border border-marble-200 bg-marble-50 shadow-sm`}
        >
          <img src={modelMeta.providerLogo} alt="" className={s.badgeIcon} />
        </span>
      )}
    </div>
  );
}
