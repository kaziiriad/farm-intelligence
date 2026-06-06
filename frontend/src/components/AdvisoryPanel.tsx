import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RiskBadge } from "@/components/RiskBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { generateAdvisory } from "@/lib/api/endpoints";
import { advisoriesKey } from "@/lib/api/queries";
import type { Advisory, AdvisoryDayScore } from "@/lib/api/types";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { toast } from "sonner";

export function AdvisoryPanel({ farmId }: { farmId: string }) {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["currentAdvisory", farmId],
    queryFn: () => generateAdvisory(farmId),
    enabled: false, // user triggers
    retry: false,
    staleTime: 60_000,
  });

  const mutation = useMutation({
    mutationFn: () => generateAdvisory(farmId),
    onSuccess: (data) => {
      qc.setQueryData(["currentAdvisory", farmId], data);
      qc.invalidateQueries({ queryKey: advisoriesKey(farmId, 20, 0) });
      qc.invalidateQueries({ queryKey: ["advisories", farmId] });
    },
    onError: (err) => {
      toast.error(apiErrorToMessage(err, "advisory"));
    },
  });

  const advisory = (query.data ?? mutation.data) as Advisory | undefined;
  const isLoading = mutation.isPending;
  const error = mutation.error ?? query.error;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <div>
          <CardTitle>7-day advisory</CardTitle>
          {advisory ? (
            <p className="text-xs text-muted-foreground mt-1">
              Generated {new Date(advisory.generated_at).toLocaleString()}
              {advisory.cached ? " · Served from cache" : ""}
            </p>
          ) : null}
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => mutation.mutate()}
          disabled={isLoading}
        >
          <RefreshCw
            className={`h-4 w-4 mr-1.5 ${isLoading ? "animate-spin" : ""}`}
          />
          {advisory ? "Refresh" : "Generate advisory"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading && !advisory ? (
          <LoadingState label="Generating advisory…" rows={2} />
        ) : error && !advisory ? (
          <ErrorState
            message={apiErrorToMessage(error, "advisory")}
            onRetry={() => mutation.mutate()}
          />
        ) : !advisory ? (
          <EmptyState
            title="No advisory yet"
            description="Generate a 7-day advisory using current WeatherAI data."
            action={
              <Button onClick={() => mutation.mutate()} disabled={isLoading}>
                Generate advisory
              </Button>
            }
          />
        ) : (
          <AdvisoryDays scores={advisory.daily_scores} />
        )}
        {advisory ? (
          <Recommendations data={advisory.recommendations} />
        ) : null}
      </CardContent>
    </Card>
  );
}

function AdvisoryDays({ scores }: { scores: AdvisoryDayScore[] }) {
  return (
    <div className="grid gap-2 grid-cols-2 sm:grid-cols-4 lg:grid-cols-7">
      {scores.map((d) => (
        <AdvisoryDayCard key={d.date} score={d} />
      ))}
    </div>
  );
}

export function AdvisoryDayCard({ score }: { score: AdvisoryDayScore }) {
  const date = new Date(score.date);
  return (
    <div className="rounded-lg border bg-card p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-xs font-medium">
          {date.toLocaleDateString(undefined, {
            weekday: "short",
            month: "short",
            day: "numeric",
          })}
        </div>
      </div>
      <RiskBadge band={score.risk_band} />
      <dl className="text-xs grid grid-cols-2 gap-x-2 gap-y-0.5 tabular-nums">
        <dt className="text-muted-foreground">Rain</dt>
        <dd className="text-right">{score.rain_score.toFixed(1)}</dd>
        <dt className="text-muted-foreground">Heat</dt>
        <dd className="text-right">{score.heat_score.toFixed(1)}</dd>
        <dt className="text-muted-foreground">Wind</dt>
        <dd className="text-right">{score.wind_score.toFixed(1)}</dd>
        <dt className="text-muted-foreground">Humidity</dt>
        <dd className="text-right">{score.humidity_score.toFixed(1)}</dd>
        <dt className="text-muted-foreground font-medium">Total</dt>
        <dd className="text-right font-medium">
          {score.total_score.toFixed(1)}
        </dd>
      </dl>
    </div>
  );
}

function Recommendations({ data }: { data: Record<string, unknown> }) {
  const keys = Object.keys(data ?? {});
  if (keys.length === 0) return null;
  return (
    <div className="mt-5 border-t pt-4">
      <h4 className="text-sm font-medium mb-2">Recommendations</h4>
      <div className="space-y-2">
        {keys.map((k) => {
          const v = data[k];
          const isPrimitive =
            typeof v === "string" || typeof v === "number" || typeof v === "boolean";
          return (
            <div key={k} className="text-sm">
              <span className="font-medium capitalize">
                {k.replace(/_/g, " ")}:{" "}
              </span>
              {isPrimitive ? (
                <span>{String(v)}</span>
              ) : (
                <details className="inline">
                  <summary className="text-muted-foreground cursor-pointer">
                    Details
                  </summary>
                  <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                    {JSON.stringify(v, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
