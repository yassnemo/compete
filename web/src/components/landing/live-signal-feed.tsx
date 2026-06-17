"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import { LabLogo, type LabSlug } from "@/components/brand-logos";
import { cn } from "@/lib/utils";

type Demo = {
  lab: LabSlug;
  company: string;
  type: string;
  title: string;
  sig: number;
};

// Self-contained demo signals - mirrors real pipeline output so the landing
// preview feels live without calling the API. Semantic tokens only, so the
// card reads correctly in both light (bone) and dark (ink) themes.
const SIGNALS: Demo[] = [
  { lab: "openai", company: "OpenAI", type: "Pricing", title: "Cuts API price 40% on flagship tier", sig: 5 },
  { lab: "anthropic", company: "Anthropic", type: "Product", title: "Ships agent SDK with computer use", sig: 5 },
  { lab: "mistral", company: "Mistral AI", type: "Hiring", title: "Opens 12 GPU infra roles in Paris", sig: 3 },
  { lab: "deepmind", company: "DeepMind", type: "Partnership", title: "Signs healthcare research alliance", sig: 4 },
  { lab: "perplexity", company: "Perplexity", type: "Launch", title: "Launches paid Pro search bundle", sig: 4 },
  { lab: "huggingface", company: "Hugging Face", type: "Product", title: "Adds enterprise model registry", sig: 3 },
  { lab: "meta", company: "Meta AI", type: "Launch", title: "Open-weights release of new model", sig: 4 },
  { lab: "gemini", company: "Gemini", type: "Pricing", title: "Bundles API credits into Pro plan", sig: 3 },
];

const VISIBLE = 7;

export function LiveSignalFeed() {
  const [start, setStart] = useState(0);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const id = setInterval(() => setStart((s) => (s + 1) % SIGNALS.length), 2600);
    return () => clearInterval(id);
  }, []);

  const rows = Array.from({ length: VISIBLE }, (_, i) => SIGNALS[(start + i) % SIGNALS.length]);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[0.7rem] font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Live signal feed
        </span>
        <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-primary" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
          </span>
          streaming
        </span>
      </div>

      {/* Overflows are clipped with a bottom fade, so the card always reads full. */}
      <div className="relative flex-1 overflow-hidden [mask-image:linear-gradient(to_bottom,black_82%,transparent)]">
        <AnimatePresence initial={false}>
          <div className="flex flex-col gap-2">
            {rows.map((s, i) => (
              <motion.div
                key={`${s.company}-${start}-${i}`}
                layout
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: i * 0.04 }}
                className="flex items-center gap-3 rounded-2xl border border-border bg-background/60 p-2.5 transition-colors hover:border-foreground/25"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-border bg-secondary text-foreground">
                  <LabLogo lab={s.lab} className="h-[18px] w-[18px]" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-semibold text-foreground">
                      {s.company}
                    </span>
                    <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                      {s.type}
                    </span>
                  </div>
                  <p className="truncate text-xs text-muted-foreground">{s.title}</p>
                </div>
                <div className="flex shrink-0 items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, d) => (
                    <span
                      key={d}
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        d < s.sig ? "bg-primary" : "bg-border",
                      )}
                    />
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>

      <p className="mt-2 text-[0.7rem] text-muted-foreground/70">Updating live · demo data</p>
    </div>
  );
}
