"use client";

import { AreaChart, DonutChart, SparkAreaChart } from "@/components/charts";
import { Activity, Bell, Building2, Signal as SignalIcon, TrendingUp, Inbox } from "lucide-react";
import Link from "next/link";

import { AsyncState } from "@/components/async-state";
import { ChartCard } from "@/components/chart-card";
import { CompetitorAvatar } from "@/components/competitor-avatar";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { RunPipelineButton } from "@/components/run-pipeline-button";
import { SignalCard } from "@/components/signal-card";
import { StatCard } from "@/components/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCompetitors, useOverview, useSignals } from "@/lib/hooks";
import { signalMeta } from "@/lib/signal-meta";

export default function OverviewPage() {
  const overview = useOverview();
  const signals = useSignals({ limit: 8 });
  const competitors = useCompetitors();

  const nameById = new Map((competitors.data ?? []).map((c) => [c.id, c.name]));
  const stats = overview.data;
  const trend = stats?.weekly_trend ?? [];

  const donutData = (stats?.by_type ?? []).map((t) => ({
    name: signalMeta(t.signal_type).label,
    value: t.count,
  }));
  const donutColors = (stats?.by_type ?? []).map((t) => signalMeta(t.signal_type).tremor);

  return (
    <div>
      <PageHeader
        title="Overview"
        description="Competitive signals across everyone you track."
        actions={<RunPipelineButton />}
      />

      {/* Metric cards: 2-up on phones, 4-up once there's room. */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard
          label="Competitors tracked"
          value={stats?.competitors_tracked ?? "-"}
          icon={Building2}
          loading={overview.isLoading}
        />
        <StatCard
          label="Signals this week"
          value={stats?.signals_this_week ?? "-"}
          icon={SignalIcon}
          hint={stats ? `${stats.signals_total} total` : undefined}
          loading={overview.isLoading}
        >
          {trend.length > 0 && (
            <SparkAreaChart
              data={trend}
              categories={["total_changes"]}
              index="week"
              colors={["lime"]}
              className="h-9 w-full"
            />
          )}
        </StatCard>
        <StatCard
          label="High significance"
          value={stats?.high_significance_count ?? "-"}
          icon={TrendingUp}
          hint="weighted ≥ 4"
          loading={overview.isLoading}
        />
        <StatCard
          label="Active alerts"
          value={stats?.active_alerts ?? "-"}
          icon={Bell}
          hint="last 7 days"
          accent={stats && stats.active_alerts > 0 ? "bg-destructive/10 text-destructive" : undefined}
          loading={overview.isLoading}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent signals feed */}
        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Recent signals
            </h2>
            <Link href="/changes" className="text-sm text-primary hover:underline">
              View all changes
            </Link>
          </div>
          <AsyncState
            isLoading={signals.isLoading}
            isError={signals.isError}
            error={signals.error}
            onRetry={() => signals.refetch()}
            isEmpty={(signals.data?.items.length ?? 0) === 0}
            skeleton={
              <div className="flex flex-col gap-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            }
            empty={
              <EmptyState
                icon={Inbox}
                title="No signals yet"
                description="Run the pipeline or seed demo data to populate the feed."
                action={<RunPipelineButton />}
              />
            }
          >
            <div className="flex flex-col gap-3">
              {signals.data?.items.map((s) => (
                <SignalCard
                  key={s.signal_id}
                  signal={s}
                  competitorName={nameById.get(s.competitor_id)}
                />
              ))}
            </div>
          </AsyncState>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-6">
          <ChartCard title="Signals by type" description="Distribution across the taxonomy">
            {overview.isLoading ? (
              <Skeleton className="h-44 w-full" />
            ) : donutData.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">No data</p>
            ) : (
              <DonutChart
                data={donutData}
                category="value"
                index="name"
                colors={donutColors}
                showAnimation
                className="h-44"
              />
            )}
          </ChartCard>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Competitors</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <AsyncState
                isLoading={competitors.isLoading}
                isError={competitors.isError}
                error={competitors.error}
                onRetry={() => competitors.refetch()}
                isEmpty={(competitors.data?.length ?? 0) === 0}
                skeleton={
                  <div className="flex flex-col gap-2">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-10 w-full" />
                    ))}
                  </div>
                }
                empty={
                  <EmptyState
                    icon={Building2}
                    title="No competitors"
                    description="Add your first competitor in Settings."
                  />
                }
              >
                <ul className="flex flex-col">
                  {competitors.data?.map((c) => (
                    <li key={c.id}>
                      <Link
                        href={`/competitors/${c.id}`}
                        className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-secondary/50"
                      >
                        <CompetitorAvatar name={c.name} id={c.id} size="sm" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-medium">{c.name}</span>
                          <span className="block text-xs text-muted-foreground">
                            {c.industry ?? c.domain ?? "-"}
                          </span>
                        </span>
                        <span className="tabular text-sm text-muted-foreground">
                          {c.signal_count}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </AsyncState>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Weekly trend */}
      <div className="mt-6">
        <ChartCard
          title="Weekly activity"
          description="Detected changes per week, with high-significance overlay"
          action={<Activity className="h-4 w-4 text-muted-foreground" />}
        >
          {overview.isLoading ? (
            <Skeleton className="h-72 w-full" />
          ) : (
            <AreaChart
              data={trend}
              index="week"
              categories={["total_changes", "high_significance_changes"]}
              colors={["lime", "stone"]}
              showAnimation
              showLegend
              yAxisWidth={36}
              className="h-72"
            />
          )}
        </ChartCard>
      </div>
    </div>
  );
}
