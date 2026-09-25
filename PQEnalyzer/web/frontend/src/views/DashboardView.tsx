import { useMemo } from "react";
import {
  MiniHist,
  SERIES_COLORS,
  Sparkline,
  type MiniGuide,
} from "../charts";
import { formatUnit, formatValue, type SummaryEntry } from "../api";
import { DriftBadge, EquilGlyph } from "../components/Stats";
import type { Mode } from "../mode";

export type SortMode = "name" | "drift";

/** Mean (solid) + median (dashed) guides for the histogram minis. */
function miniGuides(entry: SummaryEntry): MiniGuide[] {
  const guides: MiniGuide[] = [];
  if (typeof entry.combined.mean === "number") {
    guides.push({ value: entry.combined.mean, color: "#161616" });
  }
  if (typeof entry.combined.median === "number") {
    guides.push({
      value: entry.combined.median,
      color: "#8d8d8d",
      dashed: true,
    });
  }
  return guides;
}

export interface DashboardViewProps {
  summaries: SummaryEntry[];
  fileCount: number;
  mode: Mode;
  sortMode: SortMode;
  onSortMode: (next: SortMode) => void;
  parameterNames: string[];
  onInspect: (name: string) => void;
}

/** Dashboard scope: one card per parameter, click to inspect. */
export function DashboardView({
  summaries,
  fileCount,
  mode,
  sortMode,
  onSortMode,
  parameterNames,
  onInspect,
}: DashboardViewProps) {
  /** Stable series color per parameter (cards, histogram KDE). */
  const colorFor = useMemo(() => {
    const map = new Map<string, string>();
    parameterNames.forEach((name, index) => {
      map.set(name, SERIES_COLORS[index % SERIES_COLORS.length]);
    });
    return map;
  }, [parameterNames]);

  // Diagnostics trail observables (name-sorted) and never drive
  // drift order: their drift says nothing about the system state.
  const sorted = useMemo(() => {
    const observables = summaries.filter((entry) => entry.kind !== "diagnostic");
    const diagnostics = summaries
      .filter((entry) => entry.kind === "diagnostic")
      .sort((a, b) => a.name.localeCompare(b.name));
    if (sortMode === "drift") {
      observables.sort((a, b) => {
        const driftA = a.combined.drift;
        const driftB = b.combined.drift;
        if (driftA === null && driftB === null) return a.name.localeCompare(b.name);
        if (driftA === null) return 1;
        if (driftB === null) return -1;
        return Math.abs(driftB) - Math.abs(driftA);
      });
    }
    return [...observables, ...diagnostics];
  }, [summaries, sortMode]);

  return (
    <section className="setup-section">
      <div className="dash-head">
        <h2 className="section-title">
          Dashboard
          <span className="section-note">
            {summaries.length} parameters · {fileCount} file{fileCount === 1 ? "" : "s"} · click a card to inspect
          </span>
        </h2>
        <label className="dash-sort">
          Sort
          <select
            value={sortMode}
            onChange={(event) => onSortMode(event.target.value as SortMode)}
          >
            <option value="name">Name</option>
            <option value="drift">Drift</option>
          </select>
        </label>
      </div>
      <div className="spark-grid">
        {sorted.length === 0 && (
          <p className="output-empty">No parameters to summarise.</p>
        )}
        {sorted.map((entry) => {
          const color =
            colorFor.get(entry.name) ?? SERIES_COLORS[0];
          const diagnostic = entry.kind === "diagnostic";
          return (
            <button
              key={entry.name}
              type="button"
              className={`spark-card${diagnostic ? " diagnostic" : ""}`}
              title={
                diagnostic
                  ? "Diagnostic parameter (compute metadata) — no convergence analysis"
                  : undefined
              }
              data-equil={
                entry.combined.analysis?.equilibrated === undefined ||
                entry.combined.analysis?.equilibrated === null
                  ? undefined
                  : entry.combined.analysis.equilibrated
                    ? "yes"
                    : "no"
              }
              onClick={() => onInspect(entry.name)}
            >
              <span className="spark-head">
                <strong>{entry.name}</strong>
                <small>{formatUnit(entry.unit) || "n/a"}</small>
              </span>
              {mode === "histogram" && entry.hist ? (
                <MiniHist
                  edges={entry.hist.edges}
                  counts={entry.hist.counts}
                  color={color}
                  guides={miniGuides(entry)}
                />
              ) : (
                <Sparkline values={entry.spark} color={color} />
              )}
              <span className="spark-foot">
                <span>{formatValue(entry.combined.latest)}</span>
                <small>
                  {!diagnostic && (
                    <>
                      <EquilGlyph
                        equilibrated={entry.combined.analysis?.equilibrated}
                      />
                      <DriftBadge drift={entry.combined.drift} /> ·{" "}
                    </>
                  )}
                  mean {formatValue(entry.combined.mean)} ·{" "}
                  {entry.combined.rows.toLocaleString()} rows
                </small>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
