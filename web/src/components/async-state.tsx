"use client";

import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

/**
 * Standard async rendering boundary: shows a skeleton while loading, a
 * human-readable error with retry on failure, an empty state when there's no
 * data, and the children otherwise. Every list/query in the app routes through
 * this so loading/error/empty are never forgotten.
 */
export function AsyncState({
  isLoading,
  isError,
  isEmpty,
  error,
  onRetry,
  skeleton,
  empty,
  children,
}: {
  isLoading: boolean;
  isError: boolean;
  isEmpty?: boolean;
  error?: unknown;
  onRetry?: () => void;
  skeleton: ReactNode;
  empty?: ReactNode;
  children: ReactNode;
}) {
  if (isLoading) return <>{skeleton}</>;
  if (isError) {
    const message = error instanceof Error ? error.message : "Something went wrong.";
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 px-6 py-10 text-center">
        <AlertTriangle className="h-6 w-6 text-destructive" />
        <p className="mt-3 text-sm font-medium">Couldn’t load data</p>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    );
  }
  if (isEmpty && empty) return <>{empty}</>;
  return <>{children}</>;
}
