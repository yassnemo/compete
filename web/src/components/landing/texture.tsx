import type { CSSProperties } from "react";

import { cn } from "@/lib/utils";

type Mesh = "lime" | "ink";

const SRC: Record<Mesh, string> = {
  lime: "/textures/mesh-lime.svg",
  ink: "/textures/mesh-ink.svg",
};

/**
 * Decorative blurred mesh image behind a card. The blur is baked into the SVG
 * itself (feGaussianBlur), so no CSS filter is applied here: live filters on
 * large surfaces are a paint-cost trap that makes the whole page feel slow.
 * Only two variants exist on purpose - the brand is lime + ink, nothing else.
 */
export function MeshBg({
  variant = "lime",
  className,
  opacity = 0.6,
}: {
  variant?: Mesh;
  className?: string;
  opacity?: number;
}) {
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-0 z-0 bg-cover bg-center", className)}
      style={
        {
          backgroundImage: `url(${SRC[variant]})`,
          opacity,
        } as CSSProperties
      }
    />
  );
}
