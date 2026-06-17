import { Badge } from "@/components/ui/badge";
import { signalMeta } from "@/lib/signal-meta";
import type { SignalType } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SignalBadge({
  type,
  withIcon = true,
  className,
}: {
  type: SignalType | string | null;
  withIcon?: boolean;
  className?: string;
}) {
  const meta = signalMeta(type);
  const Icon = meta.icon;
  return (
    <Badge variant="outline" className={cn("border", meta.badge, className)}>
      {withIcon && <Icon className="h-3 w-3" />}
      {meta.label}
    </Badge>
  );
}
