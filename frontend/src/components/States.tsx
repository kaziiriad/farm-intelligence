import { AlertCircle, Inbox, Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState({
  label = "Loading…",
  rows = 3,
}: {
  label?: string;
  rows?: number;
}) {
  return (
    <div className="space-y-3" role="status" aria-live="polite">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{label}</span>
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="text-center border border-dashed rounded-lg p-8 bg-card">
      <div className="mx-auto h-10 w-10 flex items-center justify-center rounded-full bg-muted text-muted-foreground mb-3">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <h3 className="font-medium">{title}</h3>
      {description ? (
        <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 flex flex-col sm:flex-row sm:items-center gap-3"
    >
      <div className="flex items-start gap-2 flex-1">
        <AlertCircle className="h-4 w-4 mt-0.5 text-destructive" />
        <p className="text-sm">{message}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
