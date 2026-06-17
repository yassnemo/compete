"use client";

import { animate, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";

/**
 * Counts up from 0 to `value` once the element scrolls into view.
 * Respects prefers-reduced-motion by jumping straight to the value.
 */
export function CountUp({
  value,
  durationSeconds = 1.6,
  prefix = "",
  suffix = "",
  decimals = 0,
}: {
  value: number;
  durationSeconds?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setDisplay(value);
      return;
    }
    const controls = animate(0, value, {
      duration: durationSeconds,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(v),
    });
    return () => controls.stop();
  }, [inView, value, durationSeconds]);

  return (
    <span ref={ref} className="tabular">
      {prefix}
      {display.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}
