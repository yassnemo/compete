"use client";

import { ArrowRight, Database, Radar, ScanText, SlidersHorizontal } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Reveal } from "./reveal";
import { SectionHeader } from "./section-header";
import { MeshBg } from "./texture";

const STEPS: { n: string; icon: LucideIcon; title: string; body: string }[] = [
  { n: "01", icon: Radar, title: "Collect", body: "Crawlers snapshot competitor pages, feeds and job boards on a schedule." },
  { n: "02", icon: ScanText, title: "Extract", body: "Page diffs are sent to an LLM that returns typed, structured signals." },
  { n: "03", icon: Database, title: "Warehouse", body: "Signals land in a DuckDB + dbt warehouse with clean marts for analysis." },
  { n: "04", icon: SlidersHorizontal, title: "Rank & alert", body: "Weighted scoring ranks the moves and fires alerts above your threshold." },
];

export function HowItWorks() {
  return (
    <section id="how" className="cv-auto relative px-3 py-20 sm:px-5 sm:py-28">
      <div className="mx-auto max-w-[1640px]">
        <SectionHeader
          n="02"
          eyebrow="The process"
          title={
            <>
              Raw web pages in.{" "}
              <span className="font-serif italic text-gradient">Ranked insight out.</span>
            </>
          }
          support="Four stages, fully automated. Run it on a laptop or a free-tier cron - the pipeline doesn't care."
        />

        {/* One ink panel - same surface language as the feed and signal stream. */}
        <Reveal className="mt-12">
          <div className="grain relative overflow-hidden rounded-[2rem] border border-white/10 bg-[hsl(var(--ink))] text-[hsl(var(--bone))]">
            <MeshBg variant="ink" opacity={0.5} />

            <div className="relative flex snap-x snap-mandatory gap-0 overflow-x-auto scrollbar-thin lg:grid lg:grid-cols-4 lg:overflow-visible">
              {STEPS.map(({ n, icon: Icon, title, body }, i) => (
                <div
                  key={n}
                  className="relative flex min-w-[78vw] shrink-0 snap-center flex-col p-8 sm:min-w-[46vw] sm:p-10 lg:min-w-0 lg:shrink"
                >
                  {/* divider between steps */}
                  {i > 0 && (
                    <span className="pointer-events-none absolute inset-y-8 left-0 w-px bg-white/10" />
                  )}

                  <div className="flex items-center justify-between">
                    <span className="font-serif text-2xl italic text-lime-pop">({n})</span>
                    {i < STEPS.length - 1 && (
                      <ArrowRight className="hidden h-4 w-4 text-white/25 lg:block" />
                    )}
                  </div>

                  <span className="mt-10 grid h-12 w-12 place-items-center rounded-2xl bg-lime-pop text-[hsl(var(--ink))]">
                    <Icon className="h-5 w-5" />
                  </span>

                  <h3 className="mt-5 text-xl font-semibold tracking-tight">{title}</h3>
                  <p className="mt-2 max-w-[26ch] text-sm leading-relaxed text-white/55">{body}</p>
                </div>
              ))}
            </div>

            {/* bottom meta strip */}
            <div className="relative flex items-center justify-between border-t border-white/10 px-8 py-4 text-[0.7rem] uppercase tracking-[0.18em] text-white/40 sm:px-10">
              <span>Fully automated</span>
              <span className="hidden sm:block">~ minutes per run</span>
              <span>$0 infra to start</span>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
