"use client";

import type { ReactNode } from "react";

import { Reveal } from "./reveal";

/**
 * Shared section header so every section opens with the same editorial system:
 * numbered eyebrow on the left, oversized headline, support copy right-aligned
 * on desktop. Consistency is part of the brand.
 */
export function SectionHeader({
  n,
  eyebrow,
  title,
  support,
}: {
  n: string;
  eyebrow: string;
  title: ReactNode;
  support?: string;
}) {
  return (
    <Reveal className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="max-w-3xl">
        <p className="flex items-center gap-3 text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">
          <span className="font-serif text-base italic normal-case tracking-normal text-primary">
            ({n})
          </span>
          {eyebrow}
        </p>
        <h2 className="mt-4 text-balance text-[clamp(2rem,4vw,3.4rem)] font-semibold leading-[1.02] tracking-[-0.02em]">
          {title}
        </h2>
      </div>
      {support && (
        <p className="max-w-sm text-pretty text-muted-foreground lg:pb-1 lg:text-right">
          {support}
        </p>
      )}
    </Reveal>
  );
}
