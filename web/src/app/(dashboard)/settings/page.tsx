"use client";

import {
  Bell,
  BookOpen,
  Building2,
  Cpu,
  Monitor,
  Moon,
  Paintbrush,
  Pencil,
  Plus,
  Sun,
  Trash2,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState, type ReactNode } from "react";

import { AsyncState } from "@/components/async-state";
import { CompetitorAvatar } from "@/components/competitor-avatar";
import { CompetitorFormDialog } from "@/components/competitor-form-dialog";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useCompetitors, useDeleteCompetitor } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" description="Manage competitors, alerts, and appearance." />
      <div className="flex flex-col gap-4">
        <CompetitorsSection />
        <AlertsSection />
        <PipelineSection />
        <AppearanceSection />
        <AboutSection />
      </div>
    </div>
  );
}

/** Settings section: label column on the left, controls on the right. */
function Section({
  icon: Icon,
  title,
  description,
  action,
  children,
}: {
  icon: typeof Bell;
  title: string;
  description: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Card className="p-6 sm:p-7">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px,minmax(0,1fr)] lg:gap-10">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/15 text-foreground">
              <Icon className="h-4 w-4" />
            </span>
            <h2 className="font-semibold tracking-tight">{title}</h2>
          </div>
          <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">{description}</p>
          {action && <div className="mt-4">{action}</div>}
        </div>
        <div className="min-w-0">{children}</div>
      </div>
    </Card>
  );
}

/** A single labeled row inside a section. */
function Row({
  label,
  hint,
  children,
  border = true,
}: {
  label: string;
  hint?: ReactNode;
  children: ReactNode;
  border?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between sm:gap-6",
        border && "border-b border-border last:border-b-0",
      )}
    >
      <div className="min-w-0">
        <p className="text-sm font-medium">{label}</p>
        {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

/** Pill-style segmented control. */
function Segmented<T extends string | number>({
  value,
  onChange,
  options,
  ariaLabel,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: ReactNode }[];
  ariaLabel: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className="inline-flex items-center gap-0.5 rounded-full border border-border bg-secondary/60 p-0.5"
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={String(o.value)}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              active
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

function CompetitorsSection() {
  const competitors = useCompetitors();
  const del = useDeleteCompetitor();

  return (
    <Section
      icon={Building2}
      title="Competitors"
      description="The companies the pipeline tracks. Each one carries a tier and a set of monitored URLs."
      action={
        <CompetitorFormDialog
          trigger={
            <Button size="sm">
              <Plus className="h-4 w-4" /> Add competitor
            </Button>
          }
        />
      }
    >
      <AsyncState
        isLoading={competitors.isLoading}
        isError={competitors.isError}
        error={competitors.error}
        onRetry={() => competitors.refetch()}
        isEmpty={(competitors.data?.length ?? 0) === 0}
        skeleton={
          <div className="flex flex-col gap-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        }
        empty={
          <EmptyState
            icon={Building2}
            title="No competitors yet"
            description="Add your first competitor to start tracking."
            action={
              <CompetitorFormDialog
                trigger={
                  <Button size="sm">
                    <Plus className="h-4 w-4" /> Add your first
                  </Button>
                }
              />
            }
          />
        }
      >
        <ul className="overflow-hidden rounded-xl border border-border">
          {competitors.data?.map((c) => (
            <li
              key={c.id}
              className="flex items-center gap-3 border-b border-border bg-background/40 px-4 py-3 transition-colors last:border-b-0 hover:bg-secondary/40"
            >
              <CompetitorAvatar name={c.name} id={c.id} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{c.name}</p>
                <p className="truncate text-xs text-muted-foreground">
                  {c.tracked_url_count} URL{c.tracked_url_count === 1 ? "" : "s"} ·{" "}
                  {c.industry ?? c.domain ?? "-"}
                </p>
              </div>
              <Badge variant="muted" className="shrink-0 whitespace-nowrap">
                Tier {c.tier}
              </Badge>
              <CompetitorFormDialog
                competitor={c}
                trigger={
                  <Button variant="ghost" size="icon" aria-label={`Edit ${c.name}`}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                }
              />
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive"
                aria-label={`Remove ${c.name}`}
                disabled={del.isPending}
                onClick={() => {
                  if (confirm(`Remove ${c.name}? This cannot be undone.`)) del.mutate(c.id);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      </AsyncState>
    </Section>
  );
}

function AlertsSection() {
  // Delivery (Slack webhook / SMTP) is configured server-side via env vars.
  // These controls persist the local preference for threshold and enablement.
  const [enabled, setEnabled] = useState(false);
  const [threshold, setThreshold] = useState(4);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("compete.alerts");
    if (raw) {
      try {
        const v = JSON.parse(raw);
        setEnabled(!!v.enabled);
        setThreshold(v.threshold ?? 4);
      } catch {
        /* ignore */
      }
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (!loaded) return;
    localStorage.setItem("compete.alerts", JSON.stringify({ enabled, threshold }));
  }, [enabled, threshold, loaded]);

  return (
    <Section
      icon={Bell}
      title="Alerts"
      description="Get notified when a change crosses your significance threshold. Delivery channels (Slack, email) are configured on the server."
    >
      <Row label="Enable alerts" hint="Applies to newly extracted signals.">
        <Switch checked={enabled} onCheckedChange={setEnabled} aria-label="Enable alerts" />
      </Row>
      <Row
        label="Minimum significance"
        hint="Only changes scored at or above this level trigger an alert."
      >
        <Segmented
          ariaLabel="Minimum significance"
          value={threshold}
          onChange={setThreshold}
          options={[
            { value: 3, label: "≥ 3" },
            { value: 4, label: "≥ 4" },
            { value: 5, label: "5 only" },
          ]}
        />
      </Row>
      <Row
        label="Delivery"
        hint="Set COMPETE_SLACK_WEBHOOK or the SMTP variables in .env."
        border={false}
      >
        <Badge variant="muted">server-configured</Badge>
      </Row>
    </Section>
  );
}

function PipelineSection() {
  return (
    <Section
      icon={Cpu}
      title="Pipeline"
      description="Extraction and scheduling are configured server-side. Shown here for reference."
    >
      <Row label="LLM provider" hint="COMPETE_LLM_PROVIDER · gemini, groq, ollama, or mock.">
        <Badge variant="secondary">Gemini Flash</Badge>
      </Row>
      <Row label="Embeddings" hint="Used by the change-detection gate and the dedup mart.">
        <Badge variant="secondary">hashing (offline)</Badge>
      </Row>
      <Row label="Schedule" hint="GitHub Actions cron; also runnable on demand." border={false}>
        <Badge variant="secondary">weekly</Badge>
      </Row>
    </Section>
  );
}

function AppearanceSection() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const options = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "system", label: "System", icon: Monitor },
  ];

  return (
    <Section
      icon={Paintbrush}
      title="Appearance"
      description="Theme preference is stored in your browser and applies immediately."
    >
      <div className="grid max-w-md grid-cols-3 gap-2">
        {options.map(({ value, label, icon: Icon }) => {
          const active = mounted && theme === value;
          return (
            <button
              key={value}
              type="button"
              onClick={() => setTheme(value)}
              className={cn(
                "relative flex flex-col items-center gap-1.5 rounded-xl border p-4 text-sm transition-colors",
                active
                  ? "border-primary/60 bg-secondary"
                  : "border-border text-muted-foreground hover:bg-secondary/50",
              )}
              aria-pressed={active}
            >
              {active && (
                <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary" />
              )}
              <Icon className="h-4 w-4" />
              {label}
            </button>
          );
        })}
      </div>
    </Section>
  );
}

function AboutSection() {
  return (
    <Section
      icon={BookOpen}
      title="About"
      description="Where to look when you want to know how this works."
    >
      <Row label="Technical documentation" hint="Architecture, design decisions, and limitations.">
        <Button asChild variant="outline" size="sm">
          <a href="/docs">Open docs</a>
        </Button>
      </Row>
      <Row label="API reference" hint="Interactive OpenAPI docs served by FastAPI.">
        <Button asChild variant="outline" size="sm">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            Open API docs
          </a>
        </Button>
      </Row>
      <Row label="Data" hint="Local DuckDB warehouse with curated demo data." border={false}>
        <Badge variant="muted">v0.1 · demo</Badge>
      </Row>
    </Section>
  );
}
