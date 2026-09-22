import { useMemo, useState } from "react";
import { Modal } from "@molarverse/pq-design";
import {
  HistogramChart,
  SERIES_COLORS,
} from "../charts";
import { formatUnit, type HistogramResponse, type OverlayFlags, type SummaryResponse } from "../api";
import { TitleRow } from "../components/Chrome";
import { StatLine } from "../components/Stats";
import { HistogramDataTable } from "../components/DataTable";
import { histogramTable } from "../tables";

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

  const [dataOpen, setDataOpen] = useState(false);
  const table = useMemo(
    () => (histogram ? histogramTable(histogram) : null),
    [histogram],
  );

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
              title="Binned counts as a table"
              onClick={() => setDataOpen(true)}
            >
              Data
            </button>
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
      {summary && <StatLine stats={summary.combined} unit={summary.unit} />}
      <Modal
        open={dataOpen}
        size="full"
        title={`${focus} — binned counts`}
        subtitle={
          table ? (
            <>
              {table.bins.length} bins ·{" "}
              <a
                href={`/api/export.csv?parameter=${encodeURIComponent(focus)}`}
                download
              >
                full-resolution CSV
              </a>
            </>
          ) : undefined
        }
        onClose={() => setDataOpen(false)}
      >
        {table && <HistogramDataTable data={table} />}
      </Modal>
    </section>
  );
}
