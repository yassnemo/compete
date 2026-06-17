"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  className?: string;
  sortable?: boolean;
  sortValue?: (row: T) => string | number;
  cell: (row: T) => ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  initialSortKey,
  renderMobileCard,
}: {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T, i: number) => string;
  initialSortKey?: string;
  renderMobileCard?: (row: T) => ReactNode;
}) {
  const [sortKey, setSortKey] = useState<string | undefined>(initialSortKey);
  const [dir, setDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      if (av < bv) return dir === "asc" ? -1 : 1;
      if (av > bv) return dir === "asc" ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rows, columns, sortKey, dir]);

  function toggleSort(key: string) {
    if (sortKey === key) setDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setDir("desc");
    }
  }

  return (
    <>
      {/* Phone + tablet: cards (the table needs a wide viewport; the dashboard
          sidebar appears at md and would otherwise squeeze it). */}
      {renderMobileCard && (
        <div className="flex flex-col gap-3 lg:hidden">
          {sorted.map((row, i) => (
            <div key={getRowKey(row, i)}>{renderMobileCard(row)}</div>
          ))}
        </div>
      )}

      {/* Desktop: table */}
      <div
        className={cn(
          "scrollbar-thin overflow-x-auto rounded-lg border",
          renderMobileCard && "hidden lg:block",
        )}
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-secondary/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              {columns.map((col) => (
                <th key={col.key} className={cn("px-4 py-2.5 font-medium", col.className)}>
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(col.key)}
                      className="inline-flex items-center gap-1 hover:text-foreground"
                    >
                      {col.header}
                      {sortKey === col.key ? (
                        dir === "asc" ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : (
                          <ArrowDown className="h-3 w-3" />
                        )
                      ) : (
                        <ChevronsUpDown className="h-3 w-3 opacity-40" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr
                key={getRowKey(row, i)}
                className="border-b transition-colors last:border-0 hover:bg-secondary/30"
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn("px-4 py-3 align-top", col.className)}>
                    {col.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
