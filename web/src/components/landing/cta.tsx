"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { Reveal } from "./reveal";
import { MeshBg } from "./texture";

export function CTA() {
  return (
    <section className="cv-auto px-3 py-16 sm:px-5 sm:py-24">
      <Reveal className="mx-auto max-w-[1640px]">
        <div className="grain relative overflow-hidden rounded-[2rem] border border-white/10 bg-[hsl(var(--ink))] px-6 py-16 text-center text-[hsl(var(--bone))] sm:px-12 sm:py-28">
          <MeshBg variant="lime" opacity={0.4} className="animate-aurora" />
          <div className="pointer-events-none absolute inset-0 z-0 bg-black/25" />
          <p className="relative text-sm font-medium uppercase tracking-[0.22em] text-white/50">
            Ready when you are
          </p>
          <h2 className="relative mx-auto mt-5 max-w-3xl text-balance text-[clamp(2.2rem,6vw,5rem)] font-semibold leading-[0.98] tracking-[-0.03em]">
            Stop refreshing competitor pages.{" "}
            <span className="font-serif italic text-gradient">Let compete watch.</span>
          </h2>
          <p className="relative mx-auto mt-5 max-w-xl text-pretty text-white/60">
            Open the live dashboard and explore real signals across five frontier AI labs - seeded
            and ready to browse.
          </p>
          <div className="relative mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/dashboard"
              className="group inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground transition-transform hover:scale-[1.03]"
            >
              Open the dashboard
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-7 py-3.5 text-base font-medium text-white/90 transition-colors hover:bg-white/10"
            >
              Explore features
            </a>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
