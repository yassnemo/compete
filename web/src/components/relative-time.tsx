"use client";

import { formatDistanceToNow } from "date-fns";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

/** Hydration-safe relative timestamp; falls back to an absolute date pre-mount. */
export function RelativeTime({
  value,
  className,
}: {
  value: string | null | undefined;
  className?: string;
}) {
  const [rel, setRel] = useState<string | null>(null);
  const date = value ? new Date(value) : null;

  useEffect(() => {
    if (date) setRel(formatDistanceToNow(date, { addSuffix: true }));
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!date) return <span className={cn("text-muted-foreground", className)}>-</span>;

  const absolute = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return (
    <time
      dateTime={date.toISOString()}
      title={date.toLocaleString()}
      suppressHydrationWarning
      className={cn("tabular text-muted-foreground", className)}
    >
      {rel ?? absolute}
    </time>
  );
}
