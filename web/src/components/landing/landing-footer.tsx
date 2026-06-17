import { ArrowUpRight, Radar } from "lucide-react";
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
      <div className="mx-auto max-w-[1640px] rounded-[2rem] border border-border bg-card p-8 sm:p-12">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div className="col-span-2">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground">
                <Radar className="h-4 w-4" />
              </span>
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
    </footer>
  );
}
