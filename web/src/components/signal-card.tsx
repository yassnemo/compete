import Link from "next/link";

import { CompetitorAvatar } from "@/components/competitor-avatar";
import { RelativeTime } from "@/components/relative-time";
import { SignalBadge } from "@/components/signal-badge";
import { SignificanceDots } from "@/components/significance";
import type { Signal } from "@/lib/types";

export function SignalCard({
  signal,
  competitorName,
}: {
  signal: Signal;
  competitorName?: string;
}) {
  const name = competitorName ?? signal.competitor_id;
  return (
    <div className="flex gap-3 rounded-lg border bg-card p-4 transition-colors hover:bg-secondary/40">
      <CompetitorAvatar name={name} id={signal.competitor_id} size="sm" />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <SignalBadge type={signal.signal_type} />
          <Link
            href={`/competitors/${signal.competitor_id}`}
            className="truncate text-sm font-medium hover:underline"
          >
            {name}
          </Link>
          <span className="ml-auto flex items-center gap-2">
            <SignificanceDots value={signal.significance} />
            <RelativeTime value={signal.extracted_at} className="text-xs" />
          </span>
        </div>
        <p className="mt-1.5 line-clamp-1 text-sm font-medium">{signal.title}</p>
        {signal.summary && (
          <p className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">{signal.summary}</p>
        )}
      </div>
    </div>
  );
}
