import type { TurnEvent } from "@/lib/types"

const priorityStyles: Record<string, string> = {
  critical: "bg-terracotta/10 text-terracotta border-terracotta/20",
  important: "bg-gold/10 text-gold-dark border-gold/20",
  info: "bg-marble-200 text-marble-600 border-marble-300",
}

const priorityIcons: Record<string, string> = {
  critical: "!!!",
  important: ">>",
  info: "--",
}

interface EventChipProps {
  event: TurnEvent
}

export function EventChip({ event }: EventChipProps) {
  const style = priorityStyles[event.priority] || priorityStyles.info
  const icon = priorityIcons[event.priority] || "--"

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-sm border px-2 py-0.5 font-mono text-xs ${style}`}
    >
      <span className="opacity-50">{icon}</span>
      {event.message}
    </span>
  )
}
