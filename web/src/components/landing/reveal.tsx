"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef, type ElementType, type ReactNode } from "react";

import { cn } from "@/lib/utils";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/**
 * Scroll-triggered reveal powered by GSAP ScrollTrigger. Direct children are
 * faded/translated in with a stagger as the container enters the viewport.
 * Set `stagger` children by giving the wrapper multiple element children.
 */
export function Reveal({
  children,
  as,
  className,
  y = 28,
  stagger = 0.08,
  delay = 0,
  childSelector = ":scope > *",
  once = true,
}: {
  children: ReactNode;
  as?: ElementType;
  className?: string;
  y?: number;
  stagger?: number;
  delay?: number;
  childSelector?: string;
  once?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const Tag = (as ?? "div") as ElementType;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const targets = el.querySelectorAll<HTMLElement>(childSelector);
    if (targets.length === 0) return;

    if (reduce) {
      gsap.set(targets, { opacity: 1, y: 0 });
      return;
    }

    const ctx = gsap.context(() => {
      gsap.fromTo(
        targets,
        { opacity: 0, y, filter: "blur(6px)" },
        {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          duration: 0.9,
          delay,
          ease: "power3.out",
          stagger,
          scrollTrigger: {
            trigger: el,
            start: "top 82%",
            toggleActions: once ? "play none none none" : "play none none reverse",
          },
        },
      );
    }, el);

    return () => ctx.revert();
  }, [y, stagger, delay, childSelector, once]);

  return (
    <Tag ref={ref} className={cn(className)}>
      {children}
    </Tag>
  );
}
