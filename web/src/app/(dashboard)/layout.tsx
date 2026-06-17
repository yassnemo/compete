import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { PageTransition } from "@/components/page-transition";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell>
      <PageTransition>{children}</PageTransition>
    </AppShell>
  );
}
