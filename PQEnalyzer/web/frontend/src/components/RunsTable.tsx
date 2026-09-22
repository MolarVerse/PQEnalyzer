import { useMemo, useState } from "react";
import { formatValue, type StatBlock } from "../api";

export type RunsSortKey =
  | "label"
  | "rows"
  | "latest"
  | "mean"
  | "median"
  | "std"
  | "min"
  | "max"
  | "drift";

export const RUNS_COLUMNS: { key: RunsSortKey; label: string; numeric: boolean }[] = [
  { key: "label", label: "File", numeric: false },
  { key: "rows", label: "Rows", numeric: true },
  { key: "latest", label: "Latest", numeric: true },
  { key: "mean", label: "Mean", numeric: true },
  { key: "median", label: "Median", numeric: true },
  { key: "std", label: "σ", numeric: true },
  { key: "min", label: "Min", numeric: true },
  { key: "max", label: "Max", numeric: true },
  { key: "drift", label: "Drift", numeric: true },
];

/**
 * W&B-style sorting: nulls sink, labels sort alphabetically, numbers
 * numerically. Pure for tests; the combined row stays pinned separately.
 */
export function sortRuns(
  rows: StatBlock[],
  key: RunsSortKey,
  dir: 1 | -1,
): StatBlock[] {
  return [...rows].sort((a, b) => {
    const va = a[key];
    const vb = b[key];
    if (key === "label") {
      return dir * String(va).localeCompare(String(vb));
    }
    if (va === null && vb === null) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    return dir * (Number(va) - Number(vb));
  });
}

function cell(key: RunsSortKey, stats: StatBlock) {
  if (key === "label") return stats.label;
  if (key === "rows") return stats.rows.toLocaleString();
  const value: number | null = stats[key];
  if (key === "drift") {
    return value === null || !Number.isFinite(value)
      ? "—"
      : `${value >= 0 ? "+" : ""}${formatValue(value)}σ`;
  }
  return value === null || !Number.isFinite(value) ? "—" : formatValue(value);
}

/** Per-file stats for the focused parameter, sortable, combined pinned. */
export function RunsTable({
  files,
  combined,
}: {
  files: StatBlock[];
  combined: StatBlock;
}) {
  const [sortKey, setSortKey] = useState<RunsSortKey>("label");
  const [sortDir, setSortDir] = useState<1 | -1>(1);
  const rows = useMemo(
    () => sortRuns(files, sortKey, sortDir),
    [files, sortKey, sortDir],
  );

  const toggle = (key: RunsSortKey) => {
    if (key === sortKey) setSortDir((dir) => (dir === 1 ? -1 : 1));
    else {
      setSortKey(key);
      setSortDir(1);
    }
  };

  return (
    <div className="data-table-wrap">
      <table className="data-table runs-table">
        <thead>
          <tr>
            {RUNS_COLUMNS.map((column) => (
              <th scope="col" key={column.key} aria-sort={column.key === sortKey ? (sortDir === 1 ? "ascending" : "descending") : undefined}>
                <button
                  type="button"
                  className="runs-sort"
                  onClick={() => toggle(column.key)}
                  title={`Sort by ${column.label}`}
                >
                  {column.label}
                  {column.key === sortKey && (
                    <span aria-hidden="true">{sortDir === 1 ? " ▲" : " ▼"}</span>
                  )}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((stats) => (
            <tr key={stats.label}>
              {RUNS_COLUMNS.map((column) => (
                <td key={column.key}>
                  {column.key === "label" ? (
                    <strong>{cell(column.key, stats)}</strong>
                  ) : (
                    cell(column.key, stats)
                  )}
                </td>
              ))}
            </tr>
          ))}
          <tr className="runs-combined">
            {RUNS_COLUMNS.map((column) => (
              <td key={column.key}>
                {column.key === "label" ? (
                  <strong>{combined.label}</strong>
                ) : (
                  cell(column.key, combined)
                )}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
