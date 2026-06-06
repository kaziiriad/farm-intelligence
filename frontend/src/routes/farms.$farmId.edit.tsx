import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { FarmForm } from "@/components/FarmForm";
import { farmQuery } from "@/lib/api/queries";
import { updateFarm } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { toast } from "sonner";

export const Route = createFileRoute("/farms/$farmId/edit")({
  head: () => ({ meta: [{ title: "Edit farm · Farm Intelligence" }] }),
  component: EditFarm,
});

function EditFarm() {
  const { farmId } = Route.useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);
  const farm = useQuery(farmQuery(farmId));

  const mutation = useMutation({
    mutationFn: (values: Parameters<typeof updateFarm>[1]) =>
      updateFarm(farmId, values),
    onSuccess: () => {
      toast.success("Farm updated");
      qc.invalidateQueries({ queryKey: ["farms"] });
      qc.invalidateQueries({ queryKey: ["farm", farmId] });
      navigate({ to: "/farms/$farmId", params: { farmId } });
    },
    onError: (err) => setServerError(apiErrorToMessage(err, "farmForm")),
  });

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Edit farm</CardTitle>
          </CardHeader>
          <CardContent>
            {farm.isLoading ? (
              <LoadingState rows={3} />
            ) : farm.error ? (
              farm.error instanceof ApiError && farm.error.status === 404 ? (
                <div className="text-center py-6 space-y-3">
                  <p>Farm not found.</p>
                  <Button asChild>
                    <Link to="/farms">Back to farms</Link>
                  </Button>
                </div>
              ) : (
                <ErrorState
                  message={apiErrorToMessage(farm.error, "farm")}
                  onRetry={() => farm.refetch()}
                />
              )
            ) : farm.data ? (
              <FarmForm
                defaultValues={{
                  farmer_name: farm.data.farmer_name,
                  county: farm.data.county,
                  crop_type: farm.data.crop_type,
                  latitude: farm.data.latitude,
                  longitude: farm.data.longitude,
                  farm_size_acres: farm.data.farm_size_acres,
                }}
                submitLabel="Save changes"
                submitting={mutation.isPending}
                serverError={serverError}
                onCancel={() =>
                  navigate({ to: "/farms/$farmId", params: { farmId } })
                }
                onSubmit={(values) => {
                  setServerError(null);
                  return new Promise<void>((resolve) =>
                    mutation.mutate(values, { onSettled: () => resolve() }),
                  );
                }}
              />
            ) : null}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
