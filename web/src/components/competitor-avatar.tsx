import { LabLogo, labSlugFor } from "@/components/brand-logos";
import { cn, initials } from "@/lib/utils";

const SIZES = { sm: "h-7 w-7 text-[10px]", md: "h-9 w-9 text-xs", lg: "h-12 w-12 text-sm" };
const LOGO_SIZES = { sm: "h-3.5 w-3.5", md: "h-4 w-4", lg: "h-6 w-6" };

export function CompetitorAvatar({
  name,
  id,
  size = "md",
  className,
}: {
  name: string;
  id?: string;
  size?: keyof typeof SIZES;
  className?: string;
}) {
  // Use the official brand mark when we have it; hashed-color initials otherwise.
  const lab = labSlugFor(id ?? name) ?? labSlugFor(name);
  if (lab) {
    return (
      <span
        className={cn(
          "inline-flex shrink-0 items-center justify-center rounded-lg border bg-secondary/60 text-foreground",
          SIZES[size],
          className,
        )}
        aria-hidden
      >
        <LabLogo lab={lab} className={LOGO_SIZES[size]} />
      </span>
    );
  }

  return (
    <span
      className={cn(
        "tabular inline-flex shrink-0 items-center justify-center rounded-lg border bg-secondary/60 font-semibold text-foreground/80",
        SIZES[size],
        className,
      )}
      aria-hidden
    >
      {initials(name)}
    </span>
  );
}
