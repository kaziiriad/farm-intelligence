import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Edit, MapPin, Trash2 } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { AdvisoryPanel } from "@/components/AdvisoryPanel";
import { AdvisoryHistory } from "@/components/AdvisoryHistory";
import { OperationAdvisor } from "@/components/OperationAdvisor";
import { TreeUploadPanel } from "@/components/TreeUploadPanel";
import { TreeAnalysisHistory } from "@/components/TreeAnalysisHistory";
import { QuotaCard } from "@/components/QuotaCard";
import { FarmDeleteDialog } from "@/components/FarmDeleteDialog";
import { farmQuery, quotaQuery } from "@/lib/api/queries";
import { deleteFarm } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export const Route = createFileRoute("/farms/$farmId")({
  head: () => ({ meta: [{ title: "Farm · Farm Intelligence" }] }),
  component: FarmDetail,
});

function FarmDetail() {
  const { farmId } = Route.useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const farm = useQuery(farmQuery(farmId));
  const quota = useQuery(quotaQuery(farmId));

  const del = useMutation({
    mutationFn: () => deleteFarm(farmId),
    onSuccess: () => {
      toast.success("Farm deleted");
      qc.invalidateQueries({ queryKey: ["farms"] });
      navigate({ to: "/farms" });
    },
    onError: (err) => toast.error(apiErrorToMessage(err, "farm")),
  });

  if (farm.isLoading) {
    return (
      <AppShell>
        <LoadingState rows={4} />
      </AppShell>
    );
  }

  if (farm.error) {
    const isNotFound = farm.error instanceof ApiError && farm.error.status === 404;
    return (
      <AppShell>
        {isNotFound ? (
          <Card>
            <CardContent className="py-10 text-center space-y-3">
              <h2 className="text-xl font-semibold">Farm not found</h2>
              <p className="text-sm text-muted-foreground">
                This farm may have been deleted.
              </p>
              <Button asChild>
                <Link to="/farms">Back to farms</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <ErrorState
            message={apiErrorToMessage(farm.error, "farm")}
            onRetry={() => farm.refetch()}
          />
        )}
      </AppShell>
    );
  }

  if (!farm.data) return null;
  const f = farm.data;

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            Farm
          </div>
          <h1 className="text-2xl font-semibold">{f.farmer_name}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground mt-1">
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {f.county}
            </span>
            <span className="capitalize">{f.crop_type}</span>
            <span className="tabular-nums">
              {f.latitude.toFixed(4)}, {f.longitude.toFixed(4)}
            </span>
            {f.farm_size_acres != null ? (
              <span>{f.farm_size_acres} ac</span>
            ) : null}
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button asChild variant="outline">
            <Link to="/farms/$farmId/edit" params={{ farmId: f.id }}>
              <Edit className="h-4 w-4 mr-1.5" />
              Edit
            </Link>
          </Button>
          <Button
            variant="outline"
            onClick={() => setConfirmDelete(true)}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-1.5" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-4">
        <div className="md:col-span-1">
          {quota.isLoading ? (
            <Card>
              <CardContent className="py-6">
                <LoadingState rows={1} />
              </CardContent>
            </Card>
          ) : quota.error ? (
            <Card>
              <CardContent className="py-6">
                <ErrorState
                  message={apiErrorToMessage(quota.error, "quota")}
                  onRetry={() => quota.refetch()}
                />
              </CardContent>
            </Card>
          ) : quota.data ? (
            <QuotaCard
              title="Tree analysis quota"
              used={quota.data.used}
              limit={quota.data.limit}
              remaining={quota.data.remaining}
              tone={
                quota.data.remaining <= 0
                  ? "critical"
                  : quota.data.remaining < Math.max(1, quota.data.limit * 0.2)
                    ? "low"
                    : "healthy"
              }
            />
          ) : null}
        </div>
        <div className="md:col-span-2">
          <AdvisoryPanel farmId={f.id} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 mb-4">
        <OperationAdvisor farmId={f.id} />
        <TreeUploadPanel farmId={f.id} quota={quota.data} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <AdvisoryHistory farmId={f.id} />
        <TreeAnalysisHistory farmId={f.id} />
      </div>

      <FarmDeleteDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        farmerName={f.farmer_name}
        pending={del.isPending}
        onConfirm={() => del.mutate()}
      />
    </AppShell>
  );
}
