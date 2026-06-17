import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  accent,
  loading,
  children,
}: {
  label: string;
  value: ReactNode;
  icon: LucideIcon;
  hint?: ReactNode;
  accent?: string;
  loading?: boolean;
  children?: ReactNode;
}) {
  return (
    <Card className="p-4 transition-shadow hover:shadow-md sm:p-5">
      <div className="flex items-start justify-between gap-2 sm:gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground sm:text-sm">{label}</p>
          {loading ? (
            <Skeleton className="mt-2 h-8 w-16" />
          ) : (
            <p className="tabular mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
              {value}
            </p>
          )}
          {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
        </div>
        <span
          className={cn(
            "grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-secondary text-muted-foreground sm:h-9 sm:w-9",
            accent,
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>
      {children && <div className="mt-3">{children}</div>}
    </Card>
  );
}
