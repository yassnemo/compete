// Central, consistent styling for each signal type - used by badges, charts,
// and filters everywhere so the visual language never drifts.

import {
  Banknote,
  Briefcase,
  Circle,
  FileText,
  Megaphone,
  Rocket,
  Tag,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { SignalType } from "./types";

export interface SignalMeta {
  label: string;
  /** Badge classes (light + dark). */
  badge: string;
  /** Dot/marker background. */
  dot: string;
  /** Tremor chart color name. */
  tremor: string;
  icon: LucideIcon;
}

// Types are differentiated within the brand: a tonal ramp of greens plus warm
// neutrals, not a rainbow. Lime is reserved for the highest-traffic type.
export const SIGNAL_META: Record<SignalType, SignalMeta> = {
  pricing_change: {
    label: "Pricing",
    badge:
      "bg-lime-100 text-lime-800 border-lime-200 dark:bg-lime-500/15 dark:text-lime-300 dark:border-lime-500/25",
    dot: "bg-lime-500",
    tremor: "lime",
    icon: Tag,
  },
  product_launch: {
    label: "Launch",
    badge:
      "bg-green-100 text-green-800 border-green-200 dark:bg-green-500/15 dark:text-green-300 dark:border-green-500/25",
    dot: "bg-green-600",
    tremor: "green",
    icon: Rocket,
  },
  blog_post: {
    label: "Blog",
    badge:
      "bg-teal-100 text-teal-800 border-teal-200 dark:bg-teal-500/15 dark:text-teal-300 dark:border-teal-500/25",
    dot: "bg-teal-500",
    tremor: "teal",
    icon: FileText,
  },
  press_release: {
    label: "News",
    badge:
      "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/25",
    dot: "bg-emerald-500",
    tremor: "emerald",
    icon: Megaphone,
  },
  job_posting: {
    label: "Hiring",
    badge:
      "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-500/15 dark:text-yellow-300 dark:border-yellow-500/25",
    dot: "bg-yellow-500",
    tremor: "yellow",
    icon: Briefcase,
  },
  leadership_change: {
    label: "Leadership",
    badge:
      "bg-stone-200 text-stone-800 border-stone-300 dark:bg-stone-500/15 dark:text-stone-300 dark:border-stone-500/25",
    dot: "bg-stone-500",
    tremor: "stone",
    icon: Users,
  },
  funding_news: {
    label: "Funding",
    badge:
      "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/25",
    dot: "bg-amber-500",
    tremor: "amber",
    icon: Banknote,
  },
  other: {
    label: "Other",
    badge:
      "bg-zinc-100 text-zinc-700 border-zinc-200 dark:bg-zinc-500/15 dark:text-zinc-300 dark:border-zinc-500/25",
    dot: "bg-zinc-400",
    tremor: "zinc",
    icon: Circle,
  },
};

export function signalMeta(type: SignalType | string | null | undefined): SignalMeta {
  if (type && type in SIGNAL_META) return SIGNAL_META[type as SignalType];
  return SIGNAL_META.other;
}
