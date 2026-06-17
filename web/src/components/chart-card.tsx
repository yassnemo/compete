import type { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function ChartCard({
  title,
  description,
  action,
  className,
  children,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Card className={cn("flex flex-col", className)}>
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle className="text-base">{title}</CardTitle>
          {description && <CardDescription className="mt-1">{description}</CardDescription>}
        </div>
        {action}
      </CardHeader>
      <CardContent className="flex-1">{children}</CardContent>
    </Card>
  );
}
