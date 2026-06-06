import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/AppShell";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FarmForm } from "@/components/FarmForm";
import { createFarm } from "@/lib/api/endpoints";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { toast } from "sonner";

export const Route = createFileRoute("/farms/new")({
  head: () => ({ meta: [{ title: "Register farm · Farm Intelligence" }] }),
  component: NewFarm,
});

function NewFarm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createFarm,
    onSuccess: (farm) => {
      toast.success("Farm registered");
      qc.invalidateQueries({ queryKey: ["farms"] });
      navigate({ to: "/farms/$farmId", params: { farmId: farm.id } });
    },
    onError: (err) => {
      setServerError(apiErrorToMessage(err, "farmForm"));
    },
  });

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Register farm</CardTitle>
          </CardHeader>
          <CardContent>
            <FarmForm
              onSubmit={(values) => {
                setServerError(null);
                return new Promise<void>((resolve) =>
                  mutation.mutate(values, { onSettled: () => resolve() }),
                );
              }}
              onCancel={() => navigate({ to: "/farms" })}
              submitLabel="Register farm"
              submitting={mutation.isPending}
              serverError={serverError}
            />
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
