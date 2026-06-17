"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api } from "./api";
import type { CompetitorCreate, CompetitorUpdate, SignalQuery } from "./types";

export const keys = {
  overview: ["overview"] as const,
  competitors: ["competitors"] as const,
  competitor: (id: string) => ["competitor", id] as const,
  signals: (q: SignalQuery) => ["signals", q] as const,
  changes: (q: SignalQuery) => ["changes", q] as const,
  pricing: (id: string) => ["pricing", id] as const,
  hiring: (id: string) => ["hiring", id] as const,
  cadence: (id: string) => ["cadence", id] as const,
  reports: ["reports"] as const,
  report: (id: string) => ["report", id] as const,
};

export const useOverview = () => useQuery({ queryKey: keys.overview, queryFn: api.overview });

export const useCompetitors = () =>
  useQuery({ queryKey: keys.competitors, queryFn: api.competitors });

export const useCompetitor = (id: string) =>
  useQuery({ queryKey: keys.competitor(id), queryFn: () => api.competitor(id), enabled: !!id });

export const useSignals = (q: SignalQuery = {}) =>
  useQuery({ queryKey: keys.signals(q), queryFn: () => api.signals(q) });

export const useChanges = (q: SignalQuery = {}) =>
  useQuery({ queryKey: keys.changes(q), queryFn: () => api.changes(q) });

export const usePricing = (id: string) =>
  useQuery({ queryKey: keys.pricing(id), queryFn: () => api.pricingHistory(id), enabled: !!id });

export const useHiring = (id: string) =>
  useQuery({ queryKey: keys.hiring(id), queryFn: () => api.hiring(id), enabled: !!id });

export const useCadence = (id: string) =>
  useQuery({ queryKey: keys.cadence(id), queryFn: () => api.cadence(id), enabled: !!id });

export const useReports = () => useQuery({ queryKey: keys.reports, queryFn: api.reports });

export const useReport = (id: string) =>
  useQuery({ queryKey: keys.report(id), queryFn: () => api.report(id), enabled: !!id });

function useInvalidateCompetitors() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: keys.competitors });
    qc.invalidateQueries({ queryKey: keys.overview });
  };
}

export function useCreateCompetitor() {
  const invalidate = useInvalidateCompetitors();
  return useMutation({
    mutationFn: (body: CompetitorCreate) => api.createCompetitor(body),
    onSuccess: (c) => {
      invalidate();
      toast.success(`Added ${c.name}`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed to add competitor"),
  });
}

export function useUpdateCompetitor() {
  const invalidate = useInvalidateCompetitors();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: CompetitorUpdate }) =>
      api.updateCompetitor(id, body),
    onSuccess: (c) => {
      invalidate();
      qc.invalidateQueries({ queryKey: keys.competitor(c.id) });
      toast.success(`Updated ${c.name}`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed to update competitor"),
  });
}

export function useDeleteCompetitor() {
  const invalidate = useInvalidateCompetitors();
  return useMutation({
    mutationFn: (id: string) => api.deleteCompetitor(id),
    onSuccess: () => {
      invalidate();
      toast.success("Competitor removed");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed to remove competitor"),
  });
}

export function useRunPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { provider?: string; limit?: number }) => api.runPipeline(body),
    onSuccess: (r) => {
      toast.success("Pipeline started", { description: r.detail });
      setTimeout(() => qc.invalidateQueries(), 4000);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed to start pipeline"),
  });
}
