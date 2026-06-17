import { CTA } from "@/components/landing/cta";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";
import { LogoStrip } from "@/components/landing/logo-strip";
import { PrefetchDashboard } from "@/components/landing/prefetch-dashboard";
import { SignalsShowcase } from "@/components/landing/signals-showcase";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-clip bg-background text-foreground">
      <PrefetchDashboard />
      <LandingNav />
      <main>
        <Hero />
        <LogoStrip />
        <Features />
        <HowItWorks />
        <SignalsShowcase />
        <CTA />
      </main>
      <LandingFooter />
    </div>
  );
}
