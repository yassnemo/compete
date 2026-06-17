"use client";

import { GitCompareArrows, Inbox, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { AsyncState } from "@/components/async-state";
import { CompetitorAvatar } from "@/components/competitor-avatar";
import { Column, DataTable } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { RelativeTime } from "@/components/relative-time";
import { SignalBadge } from "@/components/signal-badge";
import { SignificanceDots } from "@/components/significance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useChanges, useCompetitors } from "@/lib/hooks";
import { SIGNAL_TYPES, type Change, type SignalQuery } from "@/lib/types";
import { signalMeta } from "@/lib/signal-meta";

// Kept inside the warm brand: green = added, amber = changed, red = removed.
const CHANGE_TYPE_BADGE: Record<string, string> = {
  new: "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-300",
  updated: "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300",
  removed: "bg-red-100 text-red-800 dark:bg-red-500/15 dark:text-red-300",
};

export default function ChangesPage() {
  const competitors = useCompetitors();
  const [filters, setFilters] = useState<SignalQuery>({ limit: 200 });

  const changes = useChanges(filters);
  const nameById = new Map((competitors.data ?? []).map((c) => [c.id, c.name]));
  const rows = changes.data?.items ?? [];

  const hasFilters =
    !!filters.competitor ||
    !!filters.signal_type ||
    !!filters.min_significance ||
    !!filters.date_from;

  function set<K extends keyof SignalQuery>(key: K, value: SignalQuery[K]) {
    setFilters((f) => ({ ...f, [key]: value || undefined }));
  }

  const columns: Column<Change>[] = [
    {
      key: "competitor",
      header: "Competitor",
      sortable: true,
      sortValue: (r) => nameById.get(r.competitor_id) ?? r.competitor_id,
      cell: (r) => (
        <Link
          href={`/competitors/${r.competitor_id}`}
          className="flex items-center gap-2 hover:underline"
        >
          <CompetitorAvatar
            name={nameById.get(r.competitor_id) ?? r.competitor_id}
            id={r.competitor_id}
            size="sm"
          />
          <span className="font-medium">{nameById.get(r.competitor_id) ?? r.competitor_id}</span>
        </Link>
      ),
    },
    {
      key: "type",
      header: "Type",
      cell: (r) => <SignalBadge type={r.signal_type} />,
    },
    {
      key: "title",
      header: "Change",
      className: "min-w-[18rem]",
      cell: (r) => (
        <div>
          <p className="font-medium">{r.title ?? "-"}</p>
          {r.summary && <p className="line-clamp-1 text-muted-foreground">{r.summary}</p>}
        </div>
      ),
    },
    {
      key: "change_type",
      header: "Kind",
      cell: (r) => (
        <Badge variant="outline" className={CHANGE_TYPE_BADGE[r.change_type] ?? ""}>
          {r.change_type}
        </Badge>
      ),
    },
    {
      key: "significance",
      header: "Significance",
      sortable: true,
      sortValue: (r) => r.weighted_significance ?? 0,
      cell: (r) => <SignificanceDots value={r.weighted_significance} />,
    },
    {
      key: "detected_at",
      header: "Detected",
      sortable: true,
      sortValue: (r) => r.detected_at ?? "",
      cell: (r) => <RelativeTime value={r.detected_at} className="text-sm" />,
    },
  ];

  return (
    <div>
      <PageHeader title="Changes" description="Every detected change, filterable and sortable." />

      {/* Filters */}
      <Card className="mb-5 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Select
            aria-label="Competitor"
            value={filters.competitor ?? ""}
            onChange={(e) => set("competitor", e.target.value)}
          >
            <option value="">All competitors</option>
            {competitors.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Signal type"
            value={filters.signal_type ?? ""}
            onChange={(e) =>
              set("signal_type", (e.target.value || undefined) as SignalQuery["signal_type"])
            }
          >
            <option value="">All types</option>
            {SIGNAL_TYPES.map((t) => (
              <option key={t} value={t}>
                {signalMeta(t).label}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Minimum significance"
            value={filters.min_significance ?? ""}
            onChange={(e) =>
              set("min_significance", e.target.value ? Number(e.target.value) : undefined)
            }
          >
            <option value="">Any significance</option>
            {[2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                ≥ {n}
              </option>
            ))}
          </Select>
          <input
            type="date"
            aria-label="From date"
            className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={filters.date_from ?? ""}
            onChange={(e) => set("date_from", e.target.value || undefined)}
          />
        </div>
        {hasFilters && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {rows.length} result{rows.length === 1 ? "" : "s"}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFilters({ limit: 200 })}
              className="h-7 px-2 text-xs"
            >
              <X className="h-3 w-3" /> Clear filters
            </Button>
          </div>
        )}
      </Card>

      <AsyncState
        isLoading={changes.isLoading}
        isError={changes.isError}
        error={changes.error}
        onRetry={() => changes.refetch()}
        isEmpty={rows.length === 0}
        skeleton={<Skeleton className="h-96 w-full" />}
        empty={
          <EmptyState
            icon={hasFilters ? Inbox : GitCompareArrows}
            title={hasFilters ? "No matching changes" : "No changes yet"}
            description={
              hasFilters
                ? "Try widening or clearing your filters."
                : "Detected changes will appear here once the pipeline runs."
            }
            action={
              hasFilters ? (
                <Button variant="outline" size="sm" onClick={() => setFilters({ limit: 200 })}>
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        }
      >
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.change_id}
          initialSortKey="detected_at"
          renderMobileCard={(r) => (
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-2">
                <SignalBadge type={r.signal_type} />
                <Badge variant="outline" className={CHANGE_TYPE_BADGE[r.change_type] ?? ""}>
                  {r.change_type}
                </Badge>
                <span className="ml-auto">
                  <SignificanceDots value={r.weighted_significance} />
                </span>
              </div>
              <p className="mt-2 text-sm font-medium">{r.title ?? "-"}</p>
              {r.summary && (
                <p className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">{r.summary}</p>
              )}
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <Link href={`/competitors/${r.competitor_id}`} className="hover:underline">
                  {nameById.get(r.competitor_id) ?? r.competitor_id}
                </Link>
                <RelativeTime value={r.detected_at} />
              </div>
            </div>
          )}
        />
      </AsyncState>
    </div>
  );
}
