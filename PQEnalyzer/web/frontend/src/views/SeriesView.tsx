import { useEffect, useMemo, useRef, useState } from "react";
import { Info } from "@molarverse/pq-design";
import { Download, RefreshCw } from "lucide-react";
import {
  Legend,
  OVERLAY_STYLES,
  SERIES_COLORS,
  type LineDataset,
} from "../charts";
import { UPlotChart, type UPlotChartHandle } from "../components/UPlotChart";
import { formatUnit, formatValue, type OverlayFlags, type OverlayItem, type SeriesResponse, type SummaryResponse } from "../api";
import { TitleRow } from "../components/Chrome";
import { AnalysisLine, StatLine } from "../components/Stats";

export interface SeriesViewProps {
  focus: string;
  unit: string;
  stale: boolean;
  autoRefresh: boolean;
  onRefresh: () => void;
  onBack: () => void;
  seriesLoading: boolean;
  series: SeriesResponse | null;
  overlays: OverlayItem[];
  overlaysLoading: boolean;
  flags: OverlayFlags;
  timeLabel: string;
  summary: SummaryResponse | null;
  overlayError: string | null;
  toolsOpen: boolean;
  onToggleTools: () => void;
}

function pngName(focus: string, kind: string) {
  return `pqenalyzer-${focus.replace(/[^\w.-]+/g, "_")}-${kind}.png`;
}

function downloadDataURL(url: string, filename: string) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

/** Focused series scope: chart, legend values, stat + analysis lines. */
export function SeriesView({
  focus,
  unit,
  stale,
  autoRefresh,
  onRefresh,
  onBack,
  seriesLoading,
  series,
  overlays,
  overlaysLoading,
  flags,
  timeLabel,
  summary,
  overlayError,
  toolsOpen,
  onToggleTools,
}: SeriesViewProps) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const mainRef = useRef<UPlotChartHandle | null>(null);
  useEffect(() => {
    setHidden(new Set());
  }, [focus, flags.autocorrelation]);

  const toggleHidden = (key: string) => {
    setHidden((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const datasets = useMemo<LineDataset[]>(() => {
    if (flags.autocorrelation) {
      return overlays.filter((overlay) => overlay.axis === "lag").map((overlay) => ({
        key: `correlation-${overlay.key}`,
        label: overlay.label,
        time: overlay.time,
        values: overlay.values,
        color: "#161616",
        width: 2,
      }));
    }
    const files = series?.series.map((item, index) => ({
          key: `file-${index}`,
          label: item.label,
          time: item.time,
          values: item.values,
          color: SERIES_COLORS[index % SERIES_COLORS.length],
          width: 1.5,
          endpoint: true,
        })) ?? [];
    const derived = overlays.filter((overlay) => overlay.axis === "time").map((overlay) => ({
      key: `overlay-${overlay.key}`,
      label: overlay.label
        .replace("Running Average", "run avg")
        .replace("Cumulative Average", "cum avg"),
      time: overlay.time,
      values: overlay.values,
      color: OVERLAY_STYLES[overlay.key]?.color ?? "#393939",
      dash: OVERLAY_STYLES[overlay.key]?.dash,
      width: OVERLAY_STYLES[overlay.key]?.width ?? 1.5,
    }));
    return [...files, ...derived];
  }, [series, overlays, flags.autocorrelation]);

  const exportPNG = () => {
    const url = mainRef.current?.exportPNG();
    if (url) downloadDataURL(url, pngName(focus, flags.autocorrelation ? "autocorrelation" : "series"));
  };

  const caption = useMemo(() => {
    if (!series) return undefined;
    const item = series.series[0];
    return `${item.rows.toLocaleString()} samples · ${series.source_count} file${series.source_count === 1 ? "" : "s"}${item.downsampled ? ` · ${item.values.length.toLocaleString()} plotted` : ""}`;
  }, [series]);

  /** MSER truncation estimate for the series chart. */
  const markers = useMemo(() => {
    const analysis = summary?.combined.analysis;
    const time = analysis?.equil_time;
    // Diagnostics have no truncation estimate.
    // Index zero means nothing to discard: no marker to draw.
    if (
      summary?.kind === "diagnostic" ||
      time === undefined ||
      time === null ||
      analysis?.equil_index === 0
    ) {
      return [];
    }
    const unitNote = series?.time_unit ? ` ${series.time_unit}` : "";
    return [{ value: time, label: `MSER ${formatValue(time)}${unitNote}` }];
  }, [summary, series]);

  /** Overlays currently on (badge on the tools button). */
  const activeOverlayCount = useMemo(
    () => Object.values(flags).filter(Boolean).length,
    [flags],
  );

  const legendItems = useMemo(
    () =>
      datasets.map((dataset) => ({
        key: dataset.key,
        label: dataset.label,
        color: dataset.color,
        dash: "dash" in dataset ? dataset.dash : undefined,
      })),
    [datasets],
  );

  return (
    <section className="setup-section">
      <TitleRow
        title={
          <>
            {focus}
            {!flags.autocorrelation && unit ? ` / ${formatUnit(unit)}` : ""}
          </>
        }
        actions={
          <>
            <button
              type="button"
              className="ghost-action"
              aria-label={`Download ${flags.autocorrelation ? "autocorrelation" : "time"} chart as PNG`}
              title={`Download ${flags.autocorrelation ? "autocorrelation" : "time"} chart as PNG`}
              onClick={exportPNG}
            >
              <Download size={14} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="ghost-action analysis-trigger"
              aria-expanded={toolsOpen}
              aria-controls="chart-tools"
              title="Choose analysis (o)"
              onClick={onToggleTools}
            >
              Analysis
              {activeOverlayCount > 0 && (
                <b className="count-badge">{activeOverlayCount}</b>
              )}
            </button>
            <button type="button" className="ghost-action refresh-action" aria-label="Refresh files" title="Refresh files" onClick={onRefresh}>
              <RefreshCw size={14} aria-hidden="true" />
            </button>
          </>
        }
        onBack={onBack}
      />
      {stale && !autoRefresh && (
        <p className="notice info" role="alert">
          <span>Files changed on disk — refresh to update.</span>
          <button type="button" onClick={onRefresh}>
            Refresh
          </button>
        </p>
      )}
      {seriesLoading && !series ? (
        <div className="chart-card" aria-label="Loading series">
          <div className="skel-chart" aria-hidden="true">
            <span className="skel-line" style={{ width: "38%" }} />
            <span className="skel-line" style={{ width: "71%" }} />
            <span className="skel-line" style={{ width: "55%" }} />
            <span className="skel-line" style={{ width: "82%" }} />
          </div>
        </div>
      ) : (
        <>
          <div className="chart-card chart-fill">
            {flags.autocorrelation && (
              <div className="chart-mode">
                <strong>Autocorrelation</strong>
                <Info text="Files combined in order. Mean-centered and normalized to 1 at lag 0. Up to half the dataset, capped at 1,000 lag steps." />
              </div>
            )}
            {!flags.autocorrelation && legendItems.length > 1 && (
              <Legend
                items={legendItems}
                hidden={hidden}
                onToggle={toggleHidden}
              />
            )}
            {flags.autocorrelation && overlaysLoading ? (
              <div className="chart-empty" role="status">Calculating…</div>
            ) : flags.autocorrelation && datasets.length === 0 ? (
              <div className="chart-empty" role="status">
                {overlayError ? "Autocorrelation unavailable." : "Requires a complete, varying series."}
              </div>
            ) : (
              <UPlotChart
                datasets={datasets}
                hidden={hidden}
                timeLabel={flags.autocorrelation ? "Lag (steps)" : `${series?.time_label ?? timeLabel}${series?.time_unit ? ` / ${series.time_unit}` : ""}`}
                integerX={flags.autocorrelation || series?.time_label === "Sample"}
                ariaLabel={flags.autocorrelation ? "Autocorrelation by lag. Drag to zoom, double-click to reset." : undefined}
                caption={flags.autocorrelation ? undefined : caption}
                markers={flags.autocorrelation ? [] : markers}
                hideFooter={flags.autocorrelation}
                resetKey={`${focus}-${flags.autocorrelation ? "lag" : "time"}`}
                ref={mainRef}
              />
            )}
          </div>
          {overlayError && (
            <p className="notice error" role="alert">
              <span>{overlayError}</span>
            </p>
          )}
          {!flags.autocorrelation && summary?.kind === "diagnostic" && (
            <p className="notice" role="note">
              <span>
                {focus} tracks the computation, not the simulated system — no
                convergence analysis. A step change here vetoes the segment;
                it never proves equilibration.
              </span>
            </p>
          )}
          {!flags.autocorrelation && summary && <StatLine stats={summary.combined} unit={summary.unit} />}
          {!flags.autocorrelation && summary && summary.kind !== "diagnostic" && (
            <AnalysisLine stats={summary.combined} />
          )}
        </>
      )}
    </section>
  );
}
