// Typed API client. Requests are proxied through Next (/api -> FastAPI) so the
// browser stays same-origin (see next.config.mjs rewrites).

import type {
  Change,
  Competitor,
  CompetitorCreate,
  CompetitorUpdate,
  CadencePoint,
  HiringRow,
  OverviewStats,
  Page,
  PricingPoint,
  Report,
  ReportSummary,
  Signal,
  SignalQuery,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body?.error?.message ?? body?.detail ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function qs(params: object): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params as Record<string, unknown>)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  overview: () => request<OverviewStats>("/stats/overview"),

  competitors: () => request<Competitor[]>("/competitors"),
  competitor: (id: string) => request<Competitor>(`/competitors/${id}`),
  createCompetitor: (body: CompetitorCreate) =>
    request<Competitor>("/competitors", { method: "POST", body: JSON.stringify(body) }),
  updateCompetitor: (id: string, body: CompetitorUpdate) =>
    request<Competitor>(`/competitors/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteCompetitor: (id: string) => request<void>(`/competitors/${id}`, { method: "DELETE" }),

  signals: (q: SignalQuery = {}) => request<Page<Signal>>(`/signals${qs(q)}`),
  changes: (q: SignalQuery = {}) => request<Page<Change>>(`/changes${qs(q)}`),

  pricingHistory: (id: string) => request<PricingPoint[]>(`/competitors/${id}/pricing-history`),
  hiring: (id: string) => request<HiringRow[]>(`/competitors/${id}/hiring`),
  cadence: (id: string) => request<CadencePoint[]>(`/competitors/${id}/cadence`),

  reports: () => request<ReportSummary[]>("/reports"),
  report: (id: string) => request<Report>(`/reports/${id}`),
  reportPdfUrl: (id: string) => `${BASE}/reports/${id}/pdf`,

  runPipeline: (body: { provider?: string; limit?: number }) =>
    request<{ status: string; detail: string }>("/pipeline/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
