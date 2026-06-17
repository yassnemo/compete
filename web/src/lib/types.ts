// TypeScript mirror of the FastAPI Pydantic schemas (see api/schemas.py).

export const SIGNAL_TYPES = [
  "pricing_change",
  "product_launch",
  "blog_post",
  "press_release",
  "job_posting",
  "leadership_change",
  "funding_news",
  "other",
] as const;
export type SignalType = (typeof SIGNAL_TYPES)[number];

export const SOURCE_TYPES = ["static", "dynamic", "rss", "jobs"] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

export interface TrackedURL {
  url: string;
  source_type: SourceType;
  signal_hint: SignalType | null;
}

export interface Competitor {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  tier: number;
  tracked_urls: TrackedURL[];
  tracked_url_count: number;
  signal_count: number;
  high_significance_count: number;
  last_signal_at: string | null;
}

export interface CompetitorCreate {
  id?: string | null;
  name: string;
  domain?: string | null;
  industry?: string | null;
  tier?: number;
  tracked_urls?: TrackedURL[];
}

export type CompetitorUpdate = Partial<Omit<CompetitorCreate, "id">>;

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Signal {
  signal_id: string;
  competitor_id: string;
  url: string | null;
  signal_type: SignalType;
  title: string | null;
  summary: string | null;
  entities: string[];
  significance: number | null;
  confidence: number | null;
  extracted_at: string | null;
}

export type ChangeType = "new" | "updated" | "removed";

export interface Change {
  change_id: string;
  competitor_id: string;
  url: string | null;
  change_type: ChangeType;
  signal_type: SignalType | null;
  title: string | null;
  summary: string | null;
  significance_score: number | null;
  weighted_significance: number | null;
  confidence: number | null;
  detected_at: string | null;
}

export interface PricingPoint {
  competitor_id: string;
  plan: string;
  price: number;
  currency: string | null;
  captured_at: string | null;
}

export interface HiringRow {
  competitor_id: string;
  role: string;
  location: string | null;
  posted_at: string | null;
  removed_at: string | null;
}

export interface CadencePoint {
  week: string;
  count: number;
}

export interface TrendPoint {
  week: string;
  total_changes: number;
  high_significance_changes: number;
}

export interface TypeCount {
  signal_type: SignalType;
  count: number;
}

export interface OverviewStats {
  competitors_tracked: number;
  signals_total: number;
  signals_this_week: number;
  high_significance_count: number;
  active_alerts: number;
  changes_this_week: number;
  by_type: TypeCount[];
  weekly_trend: TrendPoint[];
}

export interface ReportSummary {
  id: string;
  title: string;
  week_start: string | null;
  summary: string | null;
  created_at: string | null;
}

export interface Report extends ReportSummary {
  body_md: string | null;
}

export interface SignalQuery {
  competitor?: string;
  signal_type?: SignalType;
  min_significance?: number;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}
