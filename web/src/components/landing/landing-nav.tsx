"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/#features", label: "Features" },
  { href: "/#how", label: "Process" },
  { href: "/#signals", label: "Signals" },
  { href: "/docs", label: "Docs" },
];

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -28, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
      className="fixed inset-x-0 top-0 z-50 flex justify-center px-3 pt-3 sm:pt-4"
    >
      <div
        className={cn(
          "flex w-full max-w-[1640px] items-center gap-2 rounded-2xl border px-2.5 py-2 transition-all duration-500 sm:gap-3",
          scrolled
            ? "border-border bg-background/70 shadow-[0_8px_30px_-12px_rgba(0,0,0,0.25)] backdrop-blur-xl"
            : "border-transparent bg-transparent",
        )}
      >
        {/* Brand + status */}
        <Link href="/" className="group flex items-center gap-2.5 pl-1">
          <Image
            src="/compete-logo.svg"
            alt="compete logo"
            width={36}
            height={36}
            priority
            className="h-9 w-9 rounded-xl transition-transform group-hover:rotate-12"
          />
          <span className="flex flex-col leading-none">
            <span className="text-[0.95rem] font-semibold tracking-tight">compete</span>
            <span className="mt-0.5 hidden text-[0.6rem] uppercase tracking-[0.2em] text-muted-foreground sm:block">
              Intelligence
            </span>
          </span>
        </Link>

        <span className="mx-1 hidden h-7 w-px bg-border md:block" />

        {/* Links with sliding underline */}
        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="group relative rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
              <span className="absolute inset-x-3 bottom-1 h-px origin-left scale-x-0 bg-foreground transition-transform duration-300 group-hover:scale-x-100" />
            </a>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <span className="mr-1 hidden items-center gap-1.5 rounded-full border border-border bg-background/50 px-2.5 py-1 text-[0.7rem] font-medium text-muted-foreground lg:flex">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
            8 labs live
          </span>
          <ThemeToggle />
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-1.5 rounded-xl bg-foreground px-3.5 py-2 text-sm font-semibold text-background transition-colors hover:bg-foreground/90"
          >
            Open dashboard
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
