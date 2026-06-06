import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { QuotaCard } from "@/components/QuotaCard";
import { usageQuery } from "@/lib/api/queries";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/usage")({
  head: () => ({ meta: [{ title: "WeatherAI usage · Farm Intelligence" }] }),
  component: UsagePage,
});

const STATUS_STYLES: Record<string, string> = {
  healthy:
    "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-200 dark:border-emerald-800",
  low: "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-900/30 dark:text-amber-200 dark:border-amber-800",
  critical:
    "bg-red-100 text-red-900 border-red-300 dark:bg-red-900/30 dark:text-red-200 dark:border-red-800",
};

function UsagePage() {
  const usage = useQuery(usageQuery());

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6 gap-2">
        <div>
          <h1 className="text-2xl font-semibold">WeatherAI usage</h1>
          <p className="text-sm text-muted-foreground">
            Quota status across API, AI, and tree analysis requests.
          </p>
        </div>
        {usage.data ? (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
              STATUS_STYLES[usage.data.quota_status] ?? STATUS_STYLES.healthy,
            )}
            aria-label={`Quota status: ${usage.data.quota_status}`}
          >
            <span aria-hidden>●</span>
            {usage.data.quota_status}
          </span>
        ) : null}
      </div>

      {usage.isLoading ? (
        <LoadingState rows={3} />
      ) : usage.error ? (
        <Card>
          <CardContent className="py-6">
            <ErrorState
              message={apiErrorToMessage(usage.error, "usage")}
              onRetry={() => usage.refetch()}
            />
          </CardContent>
        </Card>
      ) : usage.data ? (
        <div className="grid gap-4 md:grid-cols-3">
          <QuotaCard
            title="API requests"
            used={usage.data.api.used}
            limit={usage.data.api.limit}
            remaining={usage.data.api.remaining}
          />
          <QuotaCard
            title="AI requests"
            used={usage.data.ai.used}
            limit={usage.data.ai.limit}
            remaining={usage.data.ai.remaining}
          />
          <QuotaCard
            title="Tree analyses"
            used={usage.data.trees.used}
            limit={usage.data.trees.limit}
            remaining={usage.data.trees.remaining}
          />
        </div>
      ) : null}
    </AppShell>
  );
}
