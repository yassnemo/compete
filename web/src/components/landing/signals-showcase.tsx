"use client";

import { LabLogo, type LabSlug } from "@/components/brand-logos";
import { Marquee } from "./marquee";
import { SectionHeader } from "./section-header";
import { Reveal } from "./reveal";
import { MeshBg } from "./texture";

const TYPES = [
  "Pricing",
  "Product",
  "Hiring",
  "Messaging",
  "Partnership",
  "Launch",
  "Funding",
  "Leadership",
];

const EXAMPLES: { lab: LabSlug; who: string; what: string; type: string }[] = [
  { lab: "openai", who: "OpenAI", what: "New $20 tier replaces legacy plan", type: "Pricing" },
  { lab: "anthropic", who: "Anthropic", what: "Adds prompt caching to the API", type: "Product" },
  { lab: "mistral", who: "Mistral AI", what: "Hiring spree for EU sales team", type: "Hiring" },
  { lab: "deepmind", who: "DeepMind", what: "Partners with national health service", type: "Partnership" },
  { lab: "perplexity", who: "Perplexity", what: "Ships shopping assistant in beta", type: "Launch" },
  { lab: "huggingface", who: "Hugging Face", what: "Repositions hub for enterprise", type: "Messaging" },
];

function SignalCard({ e }: { e: (typeof EXAMPLES)[number] }) {
  return (
    <div className="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur">
      <div className="flex items-center gap-2.5">
        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/[0.06] text-white">
          <LabLogo lab={e.lab} className="h-3.5 w-3.5" />
        </span>
        <span className="flex-1 truncate text-sm font-semibold text-white">{e.who}</span>
        <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-medium text-white/65">
          {e.type}
        </span>
      </div>
      <p className="mt-2 text-sm text-white/55">{e.what}</p>
    </div>
  );
}

export function SignalsShowcase() {
  const colA = [...EXAMPLES, ...EXAMPLES];
  const colB = [...EXAMPLES.slice().reverse(), ...EXAMPLES.slice().reverse()];

  return (
    <section id="signals" className="cv-auto relative px-3 py-20 sm:px-5 sm:py-28">
      <div className="mx-auto max-w-[1640px]">
        <SectionHeader
          n="03"
          eyebrow="The output"
          title={
            <>
              Every change becomes a{" "}
              <span className="font-serif italic text-gradient">typed signal.</span>
            </>
          }
          support="Instead of a wall of diffs, compete classifies each move into a clean taxonomy - filter, chart and alert on exactly what you care about."
        />

        <div className="mt-12 grid grid-cols-1 items-stretch gap-3 lg:grid-cols-12">
          <Reveal className="flex flex-col justify-center gap-7 rounded-[1.6rem] border border-border bg-card p-7 sm:p-9 lg:col-span-5">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                The taxonomy
              </p>
              <p className="mt-3 max-w-md text-pretty text-sm leading-relaxed text-muted-foreground">
                Eight signal types cover everything a competitor can do in public. Each one is
                filterable in the dashboard and scoreable for alerts.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {TYPES.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3.5 py-1.5 text-sm font-medium transition-colors hover:border-primary/60"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  {t}
                </span>
              ))}
            </div>
          </Reveal>

          {/* Inked panel with two opposing marquees of real extracted signals */}
          <div className="grain relative overflow-hidden rounded-[1.6rem] border border-white/10 bg-[hsl(var(--ink))] p-3 lg:col-span-7">
            <MeshBg variant="lime" opacity={0.15} />
            <div className="relative grid h-[420px] grid-cols-1 gap-3 [mask-image:linear-gradient(to_bottom,transparent,black_10%,black_90%,transparent)] sm:grid-cols-2">
              <Marquee vertical durationSeconds={20} className="h-full">
                {colA.map((e, i) => (
                  <SignalCard key={`a-${i}`} e={e} />
                ))}
              </Marquee>
              <Marquee vertical reverse durationSeconds={24} className="hidden h-full sm:flex">
                {colB.map((e, i) => (
                  <SignalCard key={`b-${i}`} e={e} />
                ))}
              </Marquee>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
