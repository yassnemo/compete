import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const COLS: { heading: string; links: { label: string; href: string }[] }[] = [
  {
    heading: "Explore",
    links: [
      { label: "Features", href: "/#features" },
      { label: "Process", href: "/#how" },
      { label: "Signals", href: "/#signals" },
      { label: "Documentation", href: "/docs" },
    ],
  },
  {
    heading: "App",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Changes", href: "/changes" },
      { label: "Reports", href: "/reports" },
      { label: "Settings", href: "/settings" },
    ],
  },
];

export function LandingFooter() {
  return (
    <footer className="relative overflow-hidden px-3 pb-6 pt-16 sm:px-5">
      <div className="relative mx-auto max-w-[1640px] overflow-hidden rounded-[2rem] border border-border bg-card p-8 sm:p-12">
        {/* Blurred photographic backdrop, with a card-toned scrim so the
            footer content and oversized wordmark stay legible over the image. */}
        <div aria-hidden className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
          <div
            className="absolute inset-0 scale-110 bg-cover bg-center blur-1xl"
            style={{ backgroundImage: "url(/footerBackground.jpg)", opacity: 0.3 }}
          />
          <div className="absolute inset-0 bg-gradient-to-br from-card via-card/80 to-card/40" />
        </div>

        <div className="relative z-10">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div className="col-span-2">
            <div className="flex items-center gap-2.5">
              <Image
                src="/compete-logo.svg"
                alt="compete logo"
                width={36}
                height={36}
                className="h-9 w-9 rounded-xl"
              />
              <span className="text-lg font-semibold tracking-tight">compete</span>
            </div>
            <p className="mt-4 max-w-xs text-pretty text-sm leading-relaxed text-muted-foreground">
              Competitive intelligence on autopilot. Collect, extract, rank and track every move
              your market makes.
            </p>
            <Link
              href="/dashboard"
              className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background transition-colors hover:bg-foreground/90"
            >
              Open dashboard <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          {COLS.map((col) => (
            <div key={col.heading}>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                {col.heading}
              </p>
              <ul className="mt-4 flex flex-col gap-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-sm text-foreground/80 transition-colors hover:text-foreground"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Oversized wordmark */}
        <div className="pointer-events-none mt-12 select-none overflow-hidden">
          <p className="bg-gradient-to-b from-foreground/10 to-transparent bg-clip-text text-[18vw] font-semibold leading-[0.8] tracking-[-0.04em] text-transparent">
            compete
          </p>
        </div>

        <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-sm text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} compete - a portfolio project.</p>
          <p className="inline-flex items-center gap-1.5">
            Designed &amp; built by
            <a
              href="https://yerradouani.me"
              target="_blank"
              rel="noreferrer"
              className="group inline-flex items-center gap-0.5 font-semibold text-foreground underline-offset-4 hover:underline"
            >
              Yassine Erradouani
              <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
            </a>
          </p>
        </div>
        </div>
      </div>
    </footer>
  );
}
