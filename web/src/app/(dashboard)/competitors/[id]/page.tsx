"use client";

import { AreaChart, BarChart, LineChart } from "@/components/charts";
import { ArrowLeft, Briefcase, Globe, Inbox, Layers } from "lucide-react";
import Link from "next/link";

import { AsyncState } from "@/components/async-state";
import { ChartCard } from "@/components/chart-card";
import { CompetitorAvatar } from "@/components/competitor-avatar";
import { EmptyState } from "@/components/empty-state";
import { Timeline } from "@/components/timeline";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCadence, useCompetitor, useHiring, usePricing, useSignals } from "@/lib/hooks";
import { formatPrice } from "@/lib/utils";

export default function CompetitorPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const competitor = useCompetitor(id);
  const signals = useSignals({ competitor: id, limit: 100 });
  const pricing = usePricing(id);
  const hiring = useHiring(id);
  const cadence = useCadence(id);

  const c = competitor.data;

  // Pivot pricing points into one row per date, a column per plan.
  const plans = Array.from(new Set((pricing.data ?? []).map((p) => p.plan)));
  const pricingByDate = new Map<string, Record<string, number | string>>();
  for (const p of pricing.data ?? []) {
    const d = (p.captured_at ?? "").slice(0, 10) || "-";
    const row = pricingByDate.get(d) ?? { date: d };
    row[p.plan] = p.price;
    pricingByDate.set(d, row);
  }
  const pricingData = Array.from(pricingByDate.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date)),
  );

  // Hiring counts by location (top 6).
  const locCounts = new Map<string, number>();
  for (const h of hiring.data ?? []) {
    const loc = h.location ?? "Unspecified";
    locCounts.set(loc, (locCounts.get(loc) ?? 0) + 1);
  }
  const hiringData = Array.from(locCounts, ([location, count]) => ({ location, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  return (
    <div>
      <Link
        href="/dashboard"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Overview
      </Link>

      {/* Header */}
      {competitor.isLoading ? (
        <Skeleton className="h-28 w-full" />
      ) : competitor.isError || !c ? (
        <EmptyState
          icon={Inbox}
          title="Competitor not found"
          description={competitor.error instanceof Error ? competitor.error.message : undefined}
          action={
            <Link href="/dashboard" className="text-sm text-primary hover:underline">
              Back to overview
            </Link>
          }
        />
      ) : (
        <>
          <Card className="p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <CompetitorAvatar name={c.name} id={c.id} size="lg" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight">{c.name}</h1>
                  <Badge variant="secondary">Tier {c.tier}</Badge>
                  {c.industry && <Badge variant="muted">{c.industry}</Badge>}
                </div>
                {c.domain && (
                  <a
                    href={`https://${c.domain}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
                  >
                    <Globe className="h-3.5 w-3.5" />
                    {c.domain}
                  </a>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4 sm:gap-6">
                <Stat label="Signals" value={c.signal_count} />
                <Stat label="High sig." value={c.high_significance_count} />
                <Stat label="Tracked URLs" value={c.tracked_url_count} />
              </div>
            </div>
          </Card>

          {/* Charts */}
          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartCard title="Pricing history" description="Plan prices captured over time">
              {pricing.isLoading ? (
                <Skeleton className="h-60 w-full" />
              ) : pricingData.length === 0 ? (
                <p className="py-16 text-center text-sm text-muted-foreground">
                  No pricing points detected yet.
                </p>
              ) : (
                <LineChart
                  data={pricingData}
                  index="date"
                  categories={plans}
                  colors={["lime", "emerald", "amber", "stone", "teal"]}
                  valueFormatter={(v) => formatPrice(v, "USD")}
                  showAnimation
                  yAxisWidth={44}
                  className="h-60"
                  connectNulls
                />
              )}
            </ChartCard>

            <ChartCard title="Hiring by location" description="Open roles across locations">
              {hiring.isLoading ? (
                <Skeleton className="h-60 w-full" />
              ) : hiringData.length === 0 ? (
                <p className="py-16 text-center text-sm text-muted-foreground">
                  No job postings tracked yet.
                </p>
              ) : (
                <BarChart
                  data={hiringData}
                  index="location"
                  categories={["count"]}
                  colors={["lime"]}
                  layout="vertical"
                  showAnimation
                  showLegend={false}
                  yAxisWidth={120}
                  className="h-60"
                />
              )}
            </ChartCard>

            <ChartCard
              title="Content cadence"
              description="Blog, press & launch posts per week"
              className="lg:col-span-2"
            >
              {cadence.isLoading ? (
                <Skeleton className="h-52 w-full" />
              ) : (cadence.data?.length ?? 0) === 0 ? (
                <p className="py-16 text-center text-sm text-muted-foreground">
                  No content posts tracked yet.
                </p>
              ) : (
                <AreaChart
                  data={cadence.data ?? []}
                  index="week"
                  categories={["count"]}
                  colors={["teal"]}
                  showAnimation
                  showLegend={false}
                  yAxisWidth={32}
                  className="h-52"
                />
              )}
            </ChartCard>
          </div>

          {/* Timeline */}
          <div className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Layers className="h-4 w-4 text-muted-foreground" /> Signal timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AsyncState
                  isLoading={signals.isLoading}
                  isError={signals.isError}
                  error={signals.error}
                  onRetry={() => signals.refetch()}
                  isEmpty={(signals.data?.items.length ?? 0) === 0}
                  skeleton={<Skeleton className="h-64 w-full" />}
                  empty={
                    <EmptyState
                      icon={Briefcase}
                      title="No signals yet"
                      description="Signals for this competitor will appear here."
                    />
                  }
                >
                  <Timeline signals={signals.data?.items ?? []} />
                </AsyncState>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="tabular text-2xl font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
