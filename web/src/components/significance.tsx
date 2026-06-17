import { cn } from "@/lib/utils";

// Heat scale: warm neutrals up to a clear red at 5. Severity stays readable
// without leaving the warm palette.
const LEVEL_COLOR = [
  "bg-stone-400",
  "bg-stone-400",
  "bg-amber-500",
  "bg-orange-500",
  "bg-red-500",
];

/** A 1-5 significance indicator rendered as filled dots, color-scaled by level. */
export function SignificanceDots({
  value,
  className,
}: {
  value: number | null | undefined;
  className?: string;
}) {
  const v = Math.max(0, Math.min(5, value ?? 0));
  const activeColor = LEVEL_COLOR[Math.max(0, v - 1)] ?? "bg-stone-400";
  return (
    <span
      className={cn("inline-flex items-center gap-0.5", className)}
      role="img"
      aria-label={`Significance ${v} of 5`}
      title={`Significance ${v}/5`}
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={cn(
            "h-1.5 w-1.5 rounded-full transition-colors",
            i <= v ? activeColor : "bg-muted-foreground/20",
          )}
        />
      ))}
    </span>
  );
}
