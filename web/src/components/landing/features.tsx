"use client";

import { Bell, Gauge, GitCompareArrows, Globe, LineChart, ShieldCheck } from "lucide-react";

import { Reveal } from "./reveal";
import { SectionHeader } from "./section-header";
import { MeshBg } from "./texture";

export function Features() {
  return (
    <section id="features" className="cv-auto relative px-3 py-20 sm:px-5 sm:py-28">
      <div className="mx-auto max-w-[1640px]">
        <SectionHeader
          n="01"
          eyebrow="What it does"
          title={
            <>
              A full intelligence pipeline,{" "}
              <span className="font-serif italic text-muted-foreground">not just a scraper.</span>
            </>
          }
          support="From collection to ranked, explained signals - built to feel like a calm analytics product, not another firehose."
        />

        {/* Mobile: horizontal snap carousel (keeps the page short). Desktop: bento grid. */}
        <Reveal
          className="mt-12 flex snap-x snap-mandatory gap-3 overflow-x-auto pb-3 scrollbar-thin lg:grid lg:grid-cols-6 lg:grid-rows-3 lg:overflow-visible lg:pb-0"
          stagger={0.07}
        >
          {/* Large textured feature */}
          <article className="grain group relative flex min-w-[84vw] shrink-0 snap-center flex-col justify-between overflow-hidden rounded-[1.4rem] border border-border bg-card p-7 sm:min-w-[48vw] lg:col-span-3 lg:row-span-2 lg:min-w-0 lg:shrink">
            <MeshBg
              variant="lime"
              opacity={0.4}
              className="transition-transform duration-700 group-hover:scale-[1.35]"
            />
            <div className="relative flex items-start justify-between">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[hsl(var(--ink))] text-lime-pop">
                <Globe className="h-6 w-6" />
              </span>
              <span className="font-serif text-4xl italic text-muted-foreground/40">01</span>
            </div>
            <div className="relative mt-16">
              <h3 className="text-2xl font-semibold tracking-tight">Collects everywhere</h3>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                Static pages, RSS, JS-rendered sites and ATS job boards - gathered politely, on a
                schedule, with robots respected.
              </p>
            </div>
          </article>

          <FeatureCard
            icon={Gauge}
            n="02"
            title="Extracts the meaning"
            body="LLMs turn raw page diffs into typed, structured signals - pricing, product, hiring, messaging - with summaries you can scan."
            className="lg:col-span-3"
          />

          {/* Inked feature for contrast */}
          <article className="grain group relative flex min-w-[84vw] shrink-0 snap-center flex-col justify-between overflow-hidden rounded-[1.4rem] border border-white/10 bg-[hsl(var(--ink))] p-7 text-[hsl(var(--bone))] sm:min-w-[48vw] lg:col-span-3 lg:min-w-0 lg:shrink">
            <div className="flex items-start justify-between">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-lime-pop text-[hsl(var(--ink))]">
                <LineChart className="h-5 w-5" />
              </span>
              <span className="font-serif text-3xl italic text-white/25">03</span>
            </div>
            <div className="mt-10">
              <h3 className="text-xl font-semibold tracking-tight">Ranks what matters</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/55">
                Weighted significance scoring floats the moves that change your roadmap to the top,
                and buries the noise.
              </p>
            </div>
          </article>

          <FeatureCard
            icon={GitCompareArrows}
            n="04"
            title="Tracks change over time"
            body="Pricing histories, hiring trends and content cadence per competitor - the trajectory, not just today."
            className="lg:col-span-2"
          />
          <FeatureCard
            icon={Bell}
            n="05"
            title="Alerts on the big ones"
            body="Slack and email fire only above your threshold. No daily-digest fatigue."
            mesh
            className="lg:col-span-2"
          />
          <FeatureCard
            icon={ShieldCheck}
            n="06"
            title="Yours to run"
            body="File-based DuckDB warehouse, provider-agnostic LLMs, zero lock-in."
            className="lg:col-span-2"
          />
        </Reveal>
      </div>
    </section>
  );
}

function FeatureCard({
  icon: Icon,
  n,
  title,
  body,
  mesh,
  className,
}: {
  icon: typeof Bell;
  n: string;
  title: string;
  body: string;
  mesh?: boolean;
  className?: string;
}) {
  return (
    <article
      className={`grain group relative flex min-w-[84vw] shrink-0 snap-center flex-col justify-between overflow-hidden rounded-[1.4rem] border border-border bg-card p-7 transition-all duration-300 hover:-translate-y-1 hover:border-foreground/20 sm:min-w-[48vw] lg:min-w-0 lg:shrink ${className ?? ""}`}
    >
      {mesh && (
        <MeshBg
          variant="lime"
          opacity={0.25}
          className="transition-transform duration-700 group-hover:scale-[1.3]"
        />
      )}
      <div className="relative flex items-start justify-between">
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/15 text-foreground">
          <Icon className="h-5 w-5" />
        </span>
        <span className="font-serif text-3xl italic text-muted-foreground/40">{n}</span>
      </div>
      <div className="relative mt-10">
        <h3 className="text-xl font-semibold tracking-tight">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
      </div>
    </article>
  );
}
