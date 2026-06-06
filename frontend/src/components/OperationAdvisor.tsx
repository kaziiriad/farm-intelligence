import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState, LoadingState } from "@/components/States";
import { opAdvisoryQuery } from "@/lib/api/queries";
import { OPERATION_TYPES, type OperationType } from "@/lib/api/types";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const labels: Record<OperationType, string> = {
  spraying: "Spraying",
  irrigation: "Irrigation",
  harvesting: "Harvesting",
  planting: "Planting",
  field_work: "Field work",
};

export function OperationAdvisor({ farmId }: { farmId: string }) {
  const [op, setOp] = useState<OperationType>("spraying");
  const [date, setDate] = useState<string>("");

  const query = useQuery(
    opAdvisoryQuery(farmId, op, date || undefined),
  );

  return (
    <Card>
      <CardHeader className="space-y-3">
        <CardTitle>Operation guidance</CardTitle>
        <Tabs value={op} onValueChange={(v) => setOp(v as OperationType)}>
          <TabsList className="flex flex-wrap h-auto">
            {OPERATION_TYPES.map((o) => (
              <TabsTrigger key={o} value={o}>
                {labels[o]}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="flex flex-wrap items-end gap-2">
          <div className="space-y-1">
            <Label htmlFor="op-date" className="text-xs">
              Optional date
            </Label>
            <Input
              id="op-date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-44"
            />
          </div>
          {date ? (
            <Button variant="ghost" size="sm" onClick={() => setDate("")}>
              Clear
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {query.isLoading ? (
          <LoadingState rows={1} />
        ) : query.error ? (
          <ErrorState
            message={apiErrorToMessage(query.error, "operation")}
            onRetry={() => query.refetch()}
          />
        ) : !query.data ? null : (
          <OperationResult op={op} data={query.data} />
        )}
      </CardContent>
    </Card>
  );
}

function OperationResult({
  op,
  data,
}: {
  op: OperationType;
  data: import("@/lib/api/types").OperationAdvisory;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        {data.recommended ? (
          <CheckCircle2 className="h-6 w-6 text-emerald-600 mt-0.5" />
        ) : (
          <XCircle className="h-6 w-6 text-destructive mt-0.5" />
        )}
        <div className="flex-1">
          <div className="font-medium">
            {data.recommended ? "Recommended" : "Not recommended"}
          </div>
          <div className="text-xs text-muted-foreground flex flex-wrap gap-x-3 gap-y-1 mt-1">
            {data.priority ? (
              <span>
                Priority:{" "}
                <span
                  className={cn(
                    "font-medium",
                    data.priority === "high"
                      ? "text-destructive"
                      : data.priority === "medium"
                        ? "text-amber-600 dark:text-amber-400"
                        : "text-emerald-600",
                  )}
                >
                  {data.priority}
                </span>
              </span>
            ) : null}
            {data.best_window ? <span>Best window: {data.best_window}</span> : null}
            {data.window_date ? (
              <span>
                Date:{" "}
                {new Date(data.window_date).toLocaleDateString(undefined, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </span>
            ) : null}
            {data.cached ? <span>Served from cache</span> : null}
          </div>
        </div>
      </div>

      {data.reasons.length > 0 ? (
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
            {op === "spraying"
              ? "Rain & wind factors"
              : op === "irrigation"
                ? "Irrigation drivers"
                : "Reasons"}
          </div>
          <ul className="text-sm list-disc pl-5 space-y-0.5">
            {data.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
