"use client";

import dynamic from "next/dynamic";

import { Skeleton } from "@/components/ui/skeleton";

/**
 * Tremor charts loaded as async chunks. Tremor drags in recharts (~100 kB),
 * which would otherwise sit on the critical path of every dashboard route.
 * With these wrappers the page shell paints immediately and charts hydrate a
 * beat later into a same-size skeleton, so nothing shifts.
 */

function ChartFallback() {
  return <Skeleton className="h-full min-h-[9rem] w-full" />;
}

function SparkFallback() {
  return <Skeleton className="h-9 w-full" />;
}

export const AreaChart = dynamic(() => import("@tremor/react").then((m) => m.AreaChart), {
  ssr: false,
  loading: ChartFallback,
});

export const BarChart = dynamic(() => import("@tremor/react").then((m) => m.BarChart), {
  ssr: false,
  loading: ChartFallback,
});

export const LineChart = dynamic(() => import("@tremor/react").then((m) => m.LineChart), {
  ssr: false,
  loading: ChartFallback,
});

export const DonutChart = dynamic(() => import("@tremor/react").then((m) => m.DonutChart), {
  ssr: false,
  loading: ChartFallback,
});

export const SparkAreaChart = dynamic(
  () => import("@tremor/react").then((m) => m.SparkAreaChart),
  { ssr: false, loading: SparkFallback },
);
