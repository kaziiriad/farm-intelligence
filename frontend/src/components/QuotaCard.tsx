import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export function QuotaCard({
  title,
  used,
  limit,
  remaining,
  tone,
  footer,
}: {
  title: string;
  used: number;
  limit: number;
  remaining: number;
  tone?: "healthy" | "low" | "critical";
  footer?: React.ReactNode;
}) {
  const pct =
    limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const noLimit = !(limit > 0);
  const toneCls =
    tone === "critical"
      ? "border-destructive/40"
      : tone === "low"
        ? "border-amber-400/50"
        : "";
  return (
    <Card className={cn(toneCls)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-semibold tabular-nums">
            {used.toLocaleString()}
            <span className="text-muted-foreground text-sm font-normal">
              {" "}
              / {noLimit ? "∞" : limit.toLocaleString()}
            </span>
          </div>
          <div
            className={cn(
              "text-sm tabular-nums",
              remaining <= 0
                ? "text-destructive font-medium"
                : remaining < Math.max(1, limit * 0.1)
                  ? "text-amber-600 dark:text-amber-400 font-medium"
                  : "text-muted-foreground",
            )}
          >
            {remaining.toLocaleString()} left
          </div>
        </div>
        {noLimit ? (
          <p className="text-xs text-muted-foreground">No limit configured.</p>
        ) : (
          <Progress value={pct} aria-label={`${pct}% used`} />
        )}
        {footer}
      </CardContent>
    </Card>
  );
}
