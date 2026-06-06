import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RiskBadge } from "@/components/RiskBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { advisoriesQuery } from "@/lib/api/queries";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import type { Advisory } from "@/lib/api/types";

const PAGE = 10;

export function AdvisoryHistory({ farmId }: { farmId: string }) {
  const [offset, setOffset] = useState(0);
  const query = useQuery(advisoriesQuery(farmId, PAGE, offset));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Advisory history</CardTitle>
      </CardHeader>
      <CardContent>
        {query.isLoading ? (
          <LoadingState rows={2} />
        ) : query.error ? (
          <ErrorState
            message={apiErrorToMessage(query.error, "advisory")}
            onRetry={() => query.refetch()}
          />
        ) : !query.data || query.data.items.length === 0 ? (
          <EmptyState
            title="No advisories yet"
            description="Generated advisories will appear here."
          />
        ) : (
          <>
            <ul className="divide-y">
              {query.data.items.map((a) => (
                <AdvisoryRow key={a.id} advisory={a} />
              ))}
            </ul>
            <Pager
              total={query.data.total}
              offset={offset}
              limit={PAGE}
              onChange={setOffset}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function AdvisoryRow({ advisory }: { advisory: Advisory }) {
  const [open, setOpen] = useState(false);
  const date = new Date(advisory.generated_at);
  const high = advisory.daily_scores.filter((d) => d.risk_band === "high").length;
  return (
    <li className="py-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-2 text-left"
      >
        <div>
          <div className="font-medium text-sm">{date.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground">
            {advisory.daily_scores.length} days
            {advisory.cached ? " · Cached" : ""}
            {high > 0 ? ` · ${high} high-risk day${high > 1 ? "s" : ""}` : ""}
          </div>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open ? (
        <div className="mt-3 space-y-3">
          <div className="grid gap-2 grid-cols-2 sm:grid-cols-4 lg:grid-cols-7">
            {advisory.daily_scores.map((s) => (
              <div
                key={s.date}
                className="rounded border p-2 text-xs space-y-1"
              >
                <div className="font-medium">
                  {new Date(s.date).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })}
                </div>
                <RiskBadge band={s.risk_band} />
                <div className="tabular-nums text-muted-foreground">
                  Total {s.total_score.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
          {advisory.recommendations &&
          Object.keys(advisory.recommendations).length > 0 ? (
            <details className="text-sm">
              <summary className="cursor-pointer text-muted-foreground">
                Recommendations
              </summary>
              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                {JSON.stringify(advisory.recommendations, null, 2)}
              </pre>
            </details>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

export function Pager({
  total,
  offset,
  limit,
  onChange,
}: {
  total: number;
  offset: number;
  limit: number;
  onChange: (offset: number) => void;
}) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(total, offset + limit);
  return (
    <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
      <span>
        {start}–{end} of {total}
      </span>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - limit))}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={end >= total}
          onClick={() => onChange(offset + limit)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
