"use client";

import {
  Activity,
  GitCompareArrows,
  Home,
  LayoutDashboard,
  Menu,
  Radar,
  FileText,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/changes", label: "Changes", icon: GitCompareArrows },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

function isActive(pathname: string, href: string): boolean {
  return href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);
}

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            {active && (
              <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-primary" />
            )}
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function Brand() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2 px-1 py-1">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
        <Radar className="h-4 w-4" />
      </span>
      <span className="text-base font-semibold tracking-tight">compete</span>
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r bg-card/40 px-3 py-4 md:flex">
        <Brand />
        <div className="mt-6 flex-1">
          <NavLinks pathname={pathname} />
        </div>
        <div className="px-1">
          <Link
            href="/"
            className="mb-3 inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Home className="h-3.5 w-3.5" /> Back to site
          </Link>
          <p className="px-2 text-xs text-muted-foreground">
            Competitive Intelligence
            <br />
            <span className="text-muted-foreground/60">v0.1 · demo data</span>
          </p>
        </div>
      </aside>

      <div className="md:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          {/* Mobile menu */}
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden" aria-label="Open menu">
                <Menu className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="left-0 top-0 h-full max-w-[16rem] translate-x-0 translate-y-0 rounded-none border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left">
              <Brand />
              <div className="mt-4">
                <NavLinks pathname={pathname} onNavigate={() => setOpen(false)} />
              </div>
            </DialogContent>
          </Dialog>

          <div className="flex items-center gap-2 md:hidden">
            <Activity className="h-4 w-4 text-primary" />
            <span className="font-semibold">compete</span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl px-4 pb-24 pt-6 md:px-8 md:pb-10">
          {children}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t bg-background/95 backdrop-blur md:hidden">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center gap-1 py-2 text-[11px]",
                active ? "text-primary" : "text-muted-foreground",
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
