import { useMemo } from "react";
import {
  HistogramChart,
  SERIES_COLORS,
} from "../charts";
import { formatUnit, type HistogramResponse, type OverlayFlags, type SummaryResponse } from "../api";
import { TitleRow } from "../components/Chrome";
import { StatLine } from "../components/Stats";

export interface HistogramViewProps {
  focus: string;
  unit: string;
  onBack: () => void;
  toolsOpen: boolean;
  onToggleTools: () => void;
  histogram: HistogramResponse | null;
  showKde: boolean;
  flags: OverlayFlags;
  summary: SummaryResponse | null;
}

/** Focused histogram scope: distribution, guides, KDE, stat line. */
export function HistogramView({
  focus,
  unit,
  onBack,
  toolsOpen,
  onToggleTools,
  histogram,
  showKde,
  flags,
  summary,
}: HistogramViewProps) {
  /** Guides enabled via flags (mean/median double as guide switches). */
  const visibleGuides = useMemo(() => {
    if (!histogram || (!flags.mean && !flags.median)) return [];
    return histogram.guides.filter(
      (guide) =>
        (guide.label === "Mean" && flags.mean) ||
        (guide.label === "Median" && flags.median),
    );
  }, [histogram, flags.mean, flags.median]);

  return (
    <section className="setup-section">
      <TitleRow
        title={
          <>
            {focus}
            {unit ? ` / ${formatUnit(unit)}` : ""}
          </>
        }
        actions={
          <>
            <button
              type="button"
              className="ghost-action"
              aria-expanded={toolsOpen}
              aria-controls="chart-tools"
              title="Histogram options (o)"
              onClick={onToggleTools}
            >
              Options
            </button>
          </>
        }
        onBack={onBack}
      />
      <div className="chart-card chart-fill">
        {histogram ? (
          <HistogramChart
            edges={histogram.edges}
            series={histogram.series}
            guides={visibleGuides}
            kde={showKde ? histogram.kde : []}
            fileColors={SERIES_COLORS}
          />
        ) : (
          <p className="output-empty">Computing histogram…</p>
        )}
      </div>
      {summary?.kind === "diagnostic" && (
        <p className="notice" role="note">
          <span>
            {focus} tracks the computation, not the simulated system — no
            convergence analysis. A step change here vetoes the segment;
            it never proves equilibration.
          </span>
        </p>
      )}
      {summary && <StatLine stats={summary.combined} unit={summary.unit} />}
    </section>
  );
}
