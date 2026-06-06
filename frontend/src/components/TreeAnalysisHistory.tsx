import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { Pager } from "@/components/AdvisoryHistory";
import { treeAnalysesQuery } from "@/lib/api/queries";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import type { TreeAnalysis } from "@/lib/api/types";

const PAGE = 10;

export function TreeAnalysisHistory({ farmId }: { farmId: string }) {
  const [offset, setOffset] = useState(0);
  const query = useQuery(treeAnalysesQuery(farmId, PAGE, offset));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tree analysis history</CardTitle>
      </CardHeader>
      <CardContent>
        {query.isLoading ? (
          <LoadingState rows={2} />
        ) : query.error ? (
          <ErrorState
            message={apiErrorToMessage(query.error, "generic")}
            onRetry={() => query.refetch()}
          />
        ) : !query.data || query.data.items.length === 0 ? (
          <EmptyState
            title="No tree analyses yet"
            description="Upload a tree image to see results here."
          />
        ) : (
          <>
            <ul className="divide-y">
              {query.data.items.map((t) => (
                <Row key={t.id} analysis={t} />
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

function Row({ analysis }: { analysis: TreeAnalysis }) {
  const a = analysis.analysis_result as Record<string, unknown>;
  const treeCount = typeof a?.tree_count === "number" ? a.tree_count : null;
  const canopy =
    typeof a?.canopy_health === "string" ? (a.canopy_health as string) : null;
  return (
    <li className="py-3 flex gap-3 items-start">
      {analysis.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={analysis.image_url}
          alt="Tree analysis"
          className="h-14 w-14 rounded object-cover border"
        />
      ) : (
        <div className="h-14 w-14 rounded border bg-muted" />
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium">
          {new Date(analysis.created_at).toLocaleString()}
        </div>
        <div className="text-xs text-muted-foreground">
          {treeCount != null ? `${treeCount} trees` : null}
          {treeCount != null && canopy ? " · " : null}
          {canopy ? `Canopy: ${canopy}` : null}
        </div>
        <details className="mt-1">
          <summary className="text-xs cursor-pointer text-muted-foreground">
            Raw result
          </summary>
          <pre className="text-xs bg-muted p-2 mt-1 rounded overflow-x-auto">
            {JSON.stringify(analysis.analysis_result, null, 2)}
          </pre>
        </details>
      </div>
    </li>
  );
}
