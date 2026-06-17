"use client";

import type { CSSProperties, ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * Infinite CSS marquee. Renders its children twice so the loop is seamless;
 * the keyframe translates by -50% (minus the gap). Pauses on hover.
 */
export function Marquee({
  children,
  reverse,
  vertical,
  durationSeconds = 40,
  className,
}: {
  children: ReactNode;
  reverse?: boolean;
  vertical?: boolean;
  durationSeconds?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "pause-on-hover group flex gap-3 overflow-hidden",
        vertical ? "flex-col" : "flex-row",
        className,
      )}
      style={{ "--marquee-duration": `${durationSeconds}s` } as CSSProperties}
    >
      {[0, 1].map((i) => (
        <div
          key={i}
          data-marquee
          aria-hidden={i === 1}
          className={cn(
            "flex shrink-0 gap-3",
            vertical
              ? "animate-marquee-vertical flex-col"
              : "animate-marquee flex-row",
            reverse && "[animation-direction:reverse]",
          )}
        >
          {children}
        </div>
      ))}
    </div>
  );
}
