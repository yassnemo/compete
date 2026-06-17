"use client";

import { Play, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useRunPipeline } from "@/lib/hooks";

export function RunPipelineButton() {
  const run = useRunPipeline();
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => run.mutate({ provider: "mock" })}
      disabled={run.isPending}
    >
      {run.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
      Run pipeline
    </Button>
  );
}
