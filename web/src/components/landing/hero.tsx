"use client";

import { motion, type Variants } from "framer-motion";
import { ArrowRight, TrendingUp } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { CountUp } from "./count-up";
import { LiveSignalFeed } from "./live-signal-feed";

const container: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.15 } },
};

const item: Variants = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
};

const wordItem: Variants = {
  hidden: { opacity: 0, y: "100%" },
  show: { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] } },
};

function Tile({
  children,
  className,
  grain,
}: {
  children: ReactNode;
  className?: string;
  grain?: boolean;
}) {
  return (
    <motion.div
      variants={item}
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-[1.4rem] border border-border bg-card",
        grain && "grain",
        className,
      )}
    >
      {children}
    </motion.div>
  );
}

export function Hero() {
  return (
    <section className="relative w-full px-3 pb-3 pt-24 sm:px-5 sm:pt-28">
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="mx-auto grid w-full max-w-[1640px] auto-rows-min grid-cols-1 gap-3 lg:h-[calc(100svh-9rem)] lg:grid-cols-12 lg:grid-rows-5"
      >
        {/* The pitch */}
        <Tile grain className="justify-between p-6 sm:p-10 lg:col-span-8 lg:row-span-5">
          {/* Blurred photographic backdrop, with a card-toned scrim so the
              headline and copy stay legible over the image. */}
          <div aria-hidden className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
            <div
              className="absolute inset-0 scale-110 bg-cover bg-center blur-2l"
              style={{ backgroundImage: "url(/heroBackground.jpg)", opacity: 0.3 }}
            />
            <div className="absolute inset-0 bg-gradient-to-br from-card via-card/80 to-card/40" />
          </div>
          <div className="relative">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Competitive intelligence, on autopilot
            </span>

            <h1 className="mt-7 max-w-[14ch] text-[clamp(2.7rem,6.6vw,6.4rem)] font-semibold leading-[0.95] tracking-[-0.03em]">
              {["Every", "competitor", "move,"].map((w, i) => (
                <span key={i} className="mr-[0.25em] inline-block overflow-hidden align-bottom">
                  <motion.span variants={wordItem} className="inline-block">
                    {w}
                  </motion.span>
                </span>
              ))}
              <span className="inline-block overflow-hidden align-bottom">
                <motion.span
                  variants={wordItem}
                  className="inline-block font-serif italic text-gradient"
                >
                  caught &amp; ranked.
                </motion.span>
              </span>
            </h1>
          </div>

          <div className="relative mt-8">
            <p className="max-w-md text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
              compete quietly watches pricing, hiring, launches and messaging across your market -
              then uses LLMs to surface what actually matters.
            </p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button asChild size="lg" className="rounded-full px-6 text-[0.95rem] font-semibold">
                <Link href="/dashboard">
                  Open the dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="ghost"
                size="lg"
                className="rounded-full hover:bg-foreground/5"
              >
                <a href="#how">See how it works</a>
              </Button>
              <span className="text-xs text-muted-foreground sm:ml-1">Live demo · no signup</span>
            </div>
          </div>
        </Tile>

        {/* The proof - live product output (theme-aware card) */}
        <Tile grain className="min-h-[420px] p-5 lg:col-span-4 lg:row-span-4 lg:min-h-0">
          <LiveSignalFeed />
        </Tile>

        {/* The scale */}
        <Tile className="flex-row items-center justify-between gap-4 p-6 lg:col-span-4 lg:row-span-1">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Signals parsed
            </p>
            <p className="mt-1 text-3xl font-semibold leading-none tracking-tight">
              <CountUp value={12480} />
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/15 px-3 py-1.5 text-xs font-semibold text-foreground">
            <TrendingUp className="h-3.5 w-3.5" /> +18% w/w
          </span>
        </Tile>
      </motion.div>
    </section>
  );
}
