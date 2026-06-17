"use client";

import { Plus, Trash2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useCreateCompetitor, useUpdateCompetitor } from "@/lib/hooks";
import { SIGNAL_TYPES, SOURCE_TYPES, type Competitor, type TrackedURL } from "@/lib/types";
import { signalMeta } from "@/lib/signal-meta";

interface FormState {
  name: string;
  domain: string;
  industry: string;
  tier: number;
  tracked_urls: TrackedURL[];
}

function initialState(c?: Competitor): FormState {
  return {
    name: c?.name ?? "",
    domain: c?.domain ?? "",
    industry: c?.industry ?? "",
    tier: c?.tier ?? 2,
    tracked_urls: c?.tracked_urls ?? [],
  };
}

export function CompetitorFormDialog({
  trigger,
  competitor,
}: {
  trigger: ReactNode;
  competitor?: Competitor;
}) {
  const isEdit = !!competitor;
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FormState>(initialState(competitor));
  const [errors, setErrors] = useState<Record<string, string>>({});

  const create = useCreateCompetitor();
  const update = useUpdateCompetitor();
  const pending = create.isPending || update.isPending;

  function reset() {
    setForm(initialState(competitor));
    setErrors({});
  }

  function validate(): boolean {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = "Name is required.";
    form.tracked_urls.forEach((t, i) => {
      if (t.url && !/^https?:\/\//i.test(t.url)) e[`url-${i}`] = "Must start with http(s)://";
    });
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function submit() {
    if (!validate()) return;
    const body = {
      name: form.name.trim(),
      domain: form.domain.trim() || null,
      industry: form.industry.trim() || null,
      tier: form.tier,
      tracked_urls: form.tracked_urls.filter((t) => t.url.trim()),
    };
    try {
      if (isEdit) await update.mutateAsync({ id: competitor!.id, body });
      else await create.mutateAsync(body);
      setOpen(false);
    } catch {
      /* toast handled in hook */
    }
  }

  function updateUrl(i: number, patch: Partial<TrackedURL>) {
    setForm((f) => ({
      ...f,
      tracked_urls: f.tracked_urls.map((t, idx) => (idx === i ? { ...t, ...patch } : t)),
    }));
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (o) reset();
      }}
    >
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="scrollbar-thin max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? `Edit ${competitor!.name}` : "Add competitor"}</DialogTitle>
          <DialogDescription>Track a competitor and the public URLs to monitor.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                aria-invalid={!!errors.name}
              />
              {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="domain">Domain</Label>
              <Input
                id="domain"
                placeholder="example.com"
                value={form.domain}
                onChange={(e) => setForm((f) => ({ ...f, domain: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                value={form.industry}
                onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tier">Tier</Label>
              <Select
                id="tier"
                value={form.tier}
                onChange={(e) => setForm((f) => ({ ...f, tier: Number(e.target.value) }))}
              >
                <option value={1}>Tier 1 - primary</option>
                <option value={2}>Tier 2 - secondary</option>
                <option value={3}>Tier 3 - watch</option>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Tracked URLs</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() =>
                  setForm((f) => ({
                    ...f,
                    tracked_urls: [
                      ...f.tracked_urls,
                      { url: "", source_type: "static", signal_hint: null },
                    ],
                  }))
                }
              >
                <Plus className="h-3 w-3" /> Add URL
              </Button>
            </div>
            {form.tracked_urls.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No URLs yet - add at least one to track.
              </p>
            )}
            {form.tracked_urls.map((t, i) => (
              <div key={i} className="rounded-md border p-2">
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="https://example.com/blog"
                    value={t.url}
                    onChange={(e) => updateUrl(i, { url: e.target.value })}
                    aria-invalid={!!errors[`url-${i}`]}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9 shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() =>
                      setForm((f) => ({
                        ...f,
                        tracked_urls: f.tracked_urls.filter((_, idx) => idx !== i),
                      }))
                    }
                    aria-label="Remove URL"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Select
                    value={t.source_type}
                    onChange={(e) =>
                      updateUrl(i, { source_type: e.target.value as TrackedURL["source_type"] })
                    }
                  >
                    {SOURCE_TYPES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </Select>
                  <Select
                    value={t.signal_hint ?? ""}
                    onChange={(e) =>
                      updateUrl(i, {
                        signal_hint: (e.target.value || null) as TrackedURL["signal_hint"],
                      })
                    }
                  >
                    <option value="">No hint</option>
                    {SIGNAL_TYPES.map((s) => (
                      <option key={s} value={s}>
                        {signalMeta(s).label}
                      </option>
                    ))}
                  </Select>
                </div>
                {errors[`url-${i}`] && (
                  <p className="mt-1 text-xs text-destructive">{errors[`url-${i}`]}</p>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setOpen(false)} disabled={pending}>
              Cancel
            </Button>
            <Button onClick={submit} disabled={pending}>
              {isEdit ? "Save changes" : "Add competitor"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
