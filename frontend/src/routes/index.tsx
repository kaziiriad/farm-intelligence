import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { FarmCard } from "@/components/FarmCard";
import { QuotaCard } from "@/components/QuotaCard";
import { farmsQuery, usageQuery } from "@/lib/api/queries";
import { apiErrorToMessage } from "@/lib/api/error-messages";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [{ title: "Dashboard · Farm Intelligence" }],
  }),
  component: Dashboard,
});

function Dashboard() {
  const farms = useQuery(farmsQuery(20, 0));
  const usage = useQuery(usageQuery());

  const recent = farms.data
    ? [...farms.data.items]
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )
        .slice(0, 6)
    : [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6 gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Overview of registered farms and WeatherAI usage.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/usage">View usage</Link>
          </Button>
          <Button asChild>
            <Link to="/farms/new">
              <Plus className="h-4 w-4 mr-1.5" />
              Register farm
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total farms
            </CardTitle>
          </CardHeader>
          <CardContent>
            {farms.isLoading ? (
              <LoadingState rows={1} />
            ) : farms.error ? (
              <ErrorState
                message={apiErrorToMessage(farms.error, "farmList")}
                onRetry={() => farms.refetch()}
              />
            ) : (
              <div className="text-3xl font-semibold tabular-nums">
                {farms.data?.total ?? 0}
              </div>
            )}
          </CardContent>
        </Card>

        {usage.isLoading ? (
          <Card className="md:col-span-2">
            <CardContent className="py-6">
              <LoadingState rows={1} />
            </CardContent>
          </Card>
        ) : usage.error ? (
          <Card className="md:col-span-2">
            <CardContent className="py-6">
              <ErrorState
                message={apiErrorToMessage(usage.error, "usage")}
                onRetry={() => usage.refetch()}
              />
            </CardContent>
          </Card>
        ) : usage.data ? (
          <>
            <QuotaCard
              title="AI requests"
              used={usage.data.ai.used}
              limit={usage.data.ai.limit}
              remaining={usage.data.ai.remaining}
              tone={
                usage.data.quota_status === "critical"
                  ? "critical"
                  : usage.data.quota_status === "low"
                    ? "low"
                    : "healthy"
              }
            />
            <QuotaCard
              title="Tree analyses"
              used={usage.data.trees.used}
              limit={usage.data.trees.limit}
              remaining={usage.data.trees.remaining}
            />
          </>
        ) : null}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Recent farms</CardTitle>
          <Button asChild variant="ghost" size="sm">
            <Link to="/farms">
              All farms
              <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {farms.isLoading ? (
            <LoadingState rows={3} />
          ) : farms.error ? (
            <ErrorState
              message={apiErrorToMessage(farms.error, "farmList")}
              onRetry={() => farms.refetch()}
            />
          ) : recent.length === 0 ? (
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
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {recent.map((f) => (
                <FarmCard key={f.id} farm={f} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}
