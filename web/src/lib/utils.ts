import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge conditional class names, de-duplicating Tailwind conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Initials from a competitor name, for avatar chips (e.g. "Google DeepMind" -> "GD"). */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const CURRENCY: Record<string, string> = { USD: "$", EUR: "€", GBP: "£" };

export function formatPrice(price: number, currency?: string | null): string {
  const symbol = currency ? (CURRENCY[currency] ?? "") : "";
  return `${symbol}${price % 1 === 0 ? price.toFixed(0) : price.toFixed(2)}`;
}
