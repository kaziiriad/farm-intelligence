import { cn } from "@/lib/utils";
import type { RiskBand } from "@/lib/api/types";

const cls: Record<RiskBand, string> = {
  low: "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-200 dark:border-emerald-800",
  medium:
    "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-900/30 dark:text-amber-200 dark:border-amber-800",
  high: "bg-red-100 text-red-900 border-red-300 dark:bg-red-900/30 dark:text-red-200 dark:border-red-800",
};

const labels: Record<RiskBand, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
};

export function RiskBadge({
  band,
  className,
}: {
  band: RiskBand;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        cls[band],
        className,
      )}
      aria-label={labels[band]}
    >
      <span aria-hidden="true">●</span>
      {labels[band]}
    </span>
  );
}
