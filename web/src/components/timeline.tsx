import { RelativeTime } from "@/components/relative-time";
import { SignalBadge } from "@/components/signal-badge";
import { SignificanceDots } from "@/components/significance";
import { signalMeta } from "@/lib/signal-meta";
import type { Signal } from "@/lib/types";
import { cn } from "@/lib/utils";

export function Timeline({ signals }: { signals: Signal[] }) {
  return (
    <ol className="relative ml-3 border-l border-border">
      {signals.map((s) => {
        const meta = signalMeta(s.signal_type);
        return (
          <li key={s.signal_id} className="mb-6 ml-6 last:mb-0">
            <span
              className={cn(
                "absolute -left-[7px] mt-1.5 h-3.5 w-3.5 rounded-full ring-4 ring-background",
                meta.dot,
              )}
              aria-hidden
            />
            <div className="flex flex-wrap items-center gap-2">
              <SignalBadge type={s.signal_type} />
              <SignificanceDots value={s.significance} />
              <RelativeTime value={s.extracted_at} className="ml-auto text-xs" />
            </div>
            <p className="mt-1.5 text-sm font-medium">{s.title}</p>
            {s.summary && <p className="mt-0.5 text-sm text-muted-foreground">{s.summary}</p>}
            {s.entities.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {s.entities.map((e) => (
                  <span
                    key={e}
                    className="rounded-md bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground"
                  >
                    {e}
                  </span>
                ))}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
