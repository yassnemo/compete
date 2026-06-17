import type { Config } from "tailwindcss";
import colors from "tailwindcss/colors";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{ts,tsx}",
    // Tremor module - required so its classes are generated.
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx,mjs}",
  ],
  theme: {
    transparent: "transparent",
    current: "currentColor",
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "ui-serif", "Georgia", "serif"],
      },
      colors: {
        // shadcn-style semantic tokens (HSL CSS variables; see globals.css).
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Tremor tokens (light + dark) mapped onto the lime/stone brand.
        tremor: {
          brand: {
            faint: colors.lime[50],
            muted: colors.lime[200],
            subtle: colors.lime[400],
            DEFAULT: colors.lime[600],
            emphasis: colors.lime[700],
            inverted: colors.white,
          },
          background: {
            muted: colors.stone[50],
            subtle: colors.stone[100],
            DEFAULT: colors.white,
            emphasis: colors.stone[700],
          },
          border: { DEFAULT: colors.stone[200] },
          ring: { DEFAULT: colors.stone[200] },
          content: {
            subtle: colors.stone[400],
            DEFAULT: colors.stone[500],
            emphasis: colors.stone[700],
            strong: colors.stone[900],
            inverted: colors.white,
          },
        },
        "dark-tremor": {
          brand: {
            faint: "#1a1f0e",
            muted: colors.lime[950],
            subtle: colors.lime[800],
            DEFAULT: colors.lime[500],
            emphasis: colors.lime[400],
            inverted: colors.stone[950],
          },
          background: {
            muted: "#15130f",
            subtle: colors.stone[800],
            DEFAULT: colors.stone[900],
            emphasis: colors.stone[300],
          },
          border: { DEFAULT: colors.stone[800] },
          ring: { DEFAULT: colors.stone[800] },
          content: {
            subtle: colors.stone[600],
            DEFAULT: colors.stone[500],
            emphasis: colors.stone[200],
            strong: colors.stone[50],
            inverted: colors.stone[950],
          },
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        "tremor-small": "0.375rem",
        "tremor-default": "0.5rem",
        "tremor-full": "9999px",
      },
      fontSize: {
        "tremor-label": ["0.75rem", { lineHeight: "1rem" }],
        "tremor-default": ["0.875rem", { lineHeight: "1.25rem" }],
        "tremor-title": ["1.125rem", { lineHeight: "1.75rem" }],
        "tremor-metric": ["1.875rem", { lineHeight: "2.25rem" }],
      },
      boxShadow: {
        "tremor-input": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "tremor-card": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "tremor-dropdown": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        "dark-tremor-input": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "dark-tremor-card": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "dark-tremor-dropdown": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        marquee: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(calc(-50% - 0.75rem))" },
        },
        "marquee-vertical": {
          from: { transform: "translateY(0)" },
          to: { transform: "translateY(calc(-50% - 0.75rem))" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        aurora: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(4%, -6%) scale(1.1)" },
          "66%": { transform: "translate(-4%, 4%) scale(0.95)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.7" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        marquee: "marquee var(--marquee-duration, 40s) linear infinite",
        "marquee-vertical": "marquee-vertical var(--marquee-duration, 40s) linear infinite",
        float: "float 6s ease-in-out infinite",
        aurora: "aurora 18s ease-in-out infinite",
        "pulse-ring": "pulse-ring 2.4s ease-out infinite",
      },
    },
  },
  safelist: [
    {
      pattern:
        /^(bg|text|border|ring|stroke|fill)-(lime|green|emerald|teal|yellow|amber|stone|zinc|neutral|gray|rose)-(50|100|200|300|400|500|600|700|800|900|950)$/,
      variants: ["hover", "ui-selected"],
    },
    {
      pattern: /^(text|bg|border)-(tremor|dark-tremor)-.*$/,
    },
  ],
  plugins: [require("tailwindcss-animate")],
};

export default config;
