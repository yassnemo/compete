"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api } from "@/lib/api";
import { keys } from "@/lib/hooks";

/**
 * Warms the dashboard while the visitor is still reading the landing page:
 * the route bundle via router.prefetch and the overview's three queries into
 * the shared QueryClient cache. Clicking "Open dashboard" then renders
 * immediately from cache instead of showing skeletons.
 */
export function PrefetchDashboard() {
  const qc = useQueryClient();
  const router = useRouter();

  useEffect(() => {
    const id = window.setTimeout(() => {
      router.prefetch("/dashboard");
      void qc.prefetchQuery({ queryKey: keys.overview, queryFn: api.overview });
      void qc.prefetchQuery({ queryKey: keys.competitors, queryFn: api.competitors });
      void qc.prefetchQuery({
        queryKey: keys.signals({ limit: 8 }),
        queryFn: () => api.signals({ limit: 8 }),
      });
    }, 1200);
    return () => window.clearTimeout(id);
  }, [qc, router]);

  return null;
}
