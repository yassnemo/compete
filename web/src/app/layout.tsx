import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Space_Grotesk, Instrument_Serif } from "next/font/google";

import { Providers } from "@/components/providers";
import "./globals.css";

const sans = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const serif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://compete.local"),
  title: "compete - Competitive Intelligence, on autopilot",
  description:
    "Track every move your competitors make. compete collects, extracts, and ranks meaningful signals - pricing, hiring, launches, messaging - into one calm dashboard.",
  openGraph: {
    title: "compete - Competitive Intelligence, on autopilot",
    description:
      "Track every move your competitors make. Pricing, hiring, launches, messaging - ranked and explained.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${sans.variable} ${serif.variable}`}>
      <body className="font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
