"use client";

import { LabLogo, LAB_NAMES, type LabSlug } from "@/components/brand-logos";
import { Marquee } from "./marquee";

const LABS: LabSlug[] = [
  "openai",
  "anthropic",
  "deepmind",
  "mistral",
  "perplexity",
  "meta",
  "huggingface",
  "gemini",
];

/** Slim social-proof band under the hero: who compete tracks out of the box. */
export function LogoStrip() {
  return (
    <section aria-label="Labs tracked out of the box" className="px-3 py-10 sm:px-5 sm:py-14">
      <div className="mx-auto max-w-[1640px]">
        <div className="flex flex-col items-center gap-6">
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
            Tracking the frontier - out of the box
          </p>
          <Marquee durationSeconds={36} className="mask-fade-x w-full">
            {LABS.map((lab) => (
              <span
                key={lab}
                className="flex items-center gap-2.5 whitespace-nowrap px-6 py-2 text-foreground/60 transition-colors hover:text-foreground"
              >
                <LabLogo lab={lab} className="h-6 w-6" />
                <span className="text-sm font-semibold tracking-tight">{LAB_NAMES[lab]}</span>
              </span>
            ))}
          </Marquee>
        </div>
      </div>
    </section>
  );
}
