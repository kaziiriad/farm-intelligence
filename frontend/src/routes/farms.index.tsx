import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { FarmCard } from "@/components/FarmCard";
import { Pager } from "@/components/AdvisoryHistory";
import { farmsQuery } from "@/lib/api/queries";
import { apiErrorToMessage } from "@/lib/api/error-messages";

const PAGE = 20;

export const Route = createFileRoute("/farms/")({
  head: () => ({ meta: [{ title: "Farms · Farm Intelligence" }] }),
  component: FarmsPage,
});

function FarmsPage() {
  const [offset, setOffset] = useState(0);
  const query = useQuery(farmsQuery(PAGE, offset));

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6 gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Farms</h1>
          <p className="text-sm text-muted-foreground">
            All registered farms across the workspace.
          </p>
        </div>
        <Button asChild>
          <Link to="/farms/new">
            <Plus className="h-4 w-4 mr-1.5" />
            Register farm
          </Link>
        </Button>
      </div>

      {query.isLoading ? (
        <LoadingState rows={4} />
      ) : query.error ? (
        <ErrorState
          message={apiErrorToMessage(query.error, "farmList")}
          onRetry={() => query.refetch()}
        />
      ) : !query.data || query.data.items.length === 0 ? (
        <EmptyState
          title="No farms registered yet"
          description="Register your first farm to start generating advisories."
          action={
            <Button asChild>
              <Link to="/farms/new">
                <Plus className="h-4 w-4 mr-1.5" />
                Add farm
              </Link>
            </Button>
          }
        />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {query.data.items.map((f) => (
              <FarmCard key={f.id} farm={f} />
            ))}
          </div>
          <Pager
            total={query.data.total}
            offset={offset}
            limit={PAGE}
            onChange={setOffset}
          />
        </>
      )}
    </AppShell>
  );
}
