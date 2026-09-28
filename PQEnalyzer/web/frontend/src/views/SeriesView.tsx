import { useEffect, useMemo, useRef, useState } from "react";
import { Info, Modal } from "@molarverse/pq-design";
import { Download, RefreshCw } from "lucide-react";
import {
  Legend,
  OVERLAY_STYLES,
  SERIES_COLORS,
  type LineDataset,
} from "../charts";
import { PRESETS, UPlotChart, presetRangeFor, type UPlotChartHandle } from "../components/UPlotChart";
import { formatUnit, formatValue, type OverlayFlags, type OverlayItem, type SeriesResponse, type SummaryResponse } from "../api";
import { TitleRow } from "../components/Chrome";
import { AnalysisLine, StatLine } from "../components/Stats";
import { SeriesDataTable } from "../components/DataTable";
import { RunsTable } from "../components/RunsTable";
import { seriesTable } from "../tables";
import type { TimeRange } from "../scale";

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

function downloadDataURL(url: string, filename: string) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function pngName(focus: string, kind: string) {
  return `pqenalyzer-${focus.replace(/[^\w.-]+/g, "_")}-${kind}.png`;
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
  const [dataOpen, setDataOpen] = useState(false);
  const [runsOpen, setRunsOpen] = useState(false);
  const [split, setSplit] = useState(false);
  const [splitZoom, setSplitZoom] = useState<TimeRange | null>(null);
  const mainRef = useRef<UPlotChartHandle | null>(null);
  const panelRefs = useRef(new Map<string, UPlotChartHandle | null>());
  useEffect(() => {
    setHidden(new Set());
    setDataOpen(false);
    setRunsOpen(false);
    setSplit(false);
    setSplitZoom(null);
  }, [focus]);

  useEffect(() => {
    if (flags.difference || flags.autocorrelation) {
      setSplit(false);
      setSplitZoom(null);
    }
  }, [flags.difference, flags.autocorrelation]);

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
        key: `correlation-${overlay.source_index ?? "combined"}`,
        label: series?.series[overlay.source_index ?? -1]?.label ?? overlay.label,
        time: overlay.time,
        values: overlay.values,
        color: overlay.source_index === null
          ? "#161616"
          : SERIES_COLORS[overlay.source_index % SERIES_COLORS.length],
        width: 2,
      }));
    }
    // Difference mode mirrors the desktop: raw series hide, the delta stands
    // alone. The backend likewise returns only the difference overlay.
    const showFiles = !(
      flags.difference && overlays.some((item) => item.key === "difference")
    );
    const files = showFiles
      ? (series?.series.map((item, index) => ({
          key: `file-${index}`,
          label: item.label,
          time: item.time,
          values: item.values,
          color: SERIES_COLORS[index % SERIES_COLORS.length],
          width: 1.5,
          endpoint: true,
        })) ?? [])
      : [];
    const derived = overlays.filter((overlay) => overlay.axis === "time").map((overlay) => ({
      key: `overlay-${overlay.key}-${overlay.source_index ?? "combined"}`,
      label: overlay.label
        .replace("Running Average", "run avg")
        .replace("Cumulative Average", "cum avg"),
      time: overlay.time,
      values: overlay.values,
      color: overlay.source_index === null
        ? (OVERLAY_STYLES[overlay.key]?.color ?? "#393939")
        : SERIES_COLORS[overlay.source_index % SERIES_COLORS.length],
      dash: OVERLAY_STYLES[overlay.key]?.dash,
      width: OVERLAY_STYLES[overlay.key]?.width ?? 1.5,
      sourceIndex: overlay.source_index,
    }));
    return [...files, ...derived];
  }, [series, overlays, flags.difference, flags.autocorrelation]);

  /** Small multiples: one panel per file, overlays repeated as reference. */
  const panels = useMemo(() => {
    if (!split || !series || flags.difference || flags.autocorrelation) return null;
    return series.series
      .map((item, index) => {
        const file = datasets.find((dataset) => dataset.key === `file-${index}`);
        const derived = datasets.filter((dataset) =>
          dataset.key.startsWith("overlay-") &&
          (dataset.sourceIndex === null || dataset.sourceIndex === index),
        );
        const panel = [...(file ? [file] : []), ...derived];
        if (!panel.length) return null;
        let latest: number | null = null;
        for (let i = item.values.length - 1; i >= 0; i -= 1) {
          const value = item.values[i];
          if (typeof value === "number") {
            latest = value;
            break;
          }
        }
        return {
          label: item.label,
          color: SERIES_COLORS[index % SERIES_COLORS.length],
          rows: item.rows,
          stride: item.stride,
          latest,
          datasets: panel,
        };
      })
      .filter((panel) => panel !== null);
  }, [split, series, datasets, flags.difference, flags.autocorrelation]);

  const fileCount = series?.series.length ?? 0;

  const isSplitPresetActive = (points: number | null): boolean => {
    if (points === null) return splitZoom === null;
    if (!splitZoom) return false;
    const range = presetRangeFor(
      datasets.filter((dataset) => !hidden.has(dataset.key)),
      points,
    );
    return (
      range !== null &&
      Math.abs(range.t0 - Math.min(splitZoom.t0, splitZoom.t1)) < 1e-9 &&
      Math.abs(range.t1 - Math.max(splitZoom.t0, splitZoom.t1)) < 1e-9
    );
  };

  const exportPNG = () => {
    if (panels) {
      const urls = [...panelRefs.current.values()]
        .map((handle) => handle?.exportPNG())
        .filter((url): url is string => !!url);
      if (!urls.length) return;
      if (urls.length === 1) {
        downloadDataURL(urls[0], pngName(focus, "split"));
        return;
      }
      const images = urls.map((url) => {
        const image = new Image();
        image.src = url;
        return image;
      });
      Promise.all(images.map((image) => image.decode()))
        .then(() => {
          const canvas = document.createElement("canvas");
          canvas.width = Math.max(...images.map((image) => image.naturalWidth));
          canvas.height = images.reduce(
            (total, image) => total + image.naturalHeight,
            0,
          );
          const context = canvas.getContext("2d");
          if (!context) return;
          context.fillStyle = "#ffffff";
          context.fillRect(0, 0, canvas.width, canvas.height);
          let top = 0;
          for (const image of images) {
            context.drawImage(image, 0, top);
            top += image.naturalHeight;
          }
          downloadDataURL(canvas.toDataURL("image/png"), pngName(focus, "split"));
        })
        .catch(() => {
          /* canvas unavailable: no download, no crash */
        });
      return;
    }
    const url = mainRef.current?.exportPNG();
    if (url) downloadDataURL(url, pngName(focus, flags.autocorrelation ? "autocorrelation" : "series"));
  };

  const caption = useMemo(() => {
    if (!series) return undefined;
    const rows = series.series.reduce((total, item) => total + item.rows, 0);
    const strides = [...new Set(series.series.map((item) => item.stride))];
    const strideNote =
      strides.length === 1 && strides[0] > 1
        ? ` · stride ${strides[0]}`
        : "";
    const times = series.series.flatMap((item) => item.time).filter(
      (t): t is number => typeof t === "number",
    );
    let spanNote = "";
    if (times.length >= 2) {
      const ordered = [...times].sort((a, b) => a - b);
      const span = ordered[ordered.length - 1] - ordered[0];
      const diffs = series.series.flatMap((item) => {
        const runTimes = item.time.filter((t): t is number => typeof t === "number");
        return runTimes.slice(1).map((t, i) => t - runTimes[i]).filter((dt) => dt > 0);
      });
      const dt = diffs.sort((a, b) => a - b)[Math.floor(diffs.length / 2)];
      const unitNote = series.time_unit ? ` ${series.time_unit}` : "";
      spanNote = ` · ${diffs.length ? `Δt ${formatValue(dt)}${unitNote} · ` : ""}span ${formatValue(span)}${unitNote}`;
    }
    return `${rows.toLocaleString()} samples · ${series.series.length} run${series.series.length === 1 ? "" : "s"}${strideNote}${spanNote}`;
  }, [series]);

  /** MSER marker for the series chart (equilibration point). */
  const markers = useMemo(() => {
    const analysis = summary?.combined.analysis;
    const time = analysis?.equil_time;
    // Diagnostics get no convergence verdicts, hence no marker either.
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
    return [{ value: time, label: `equil ${formatValue(time)}${unitNote}` }];
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

  /** Transported-points table (built once per load, not per render). */
  const table = useMemo(
    () => (series ? seriesTable(series) : null),
    [series],
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
              title="Transported data points as a table"
              onClick={() => setDataOpen(true)}
            >
              Data
            </button>
            {summary && summary.files.length > 0 && (
              <button
                type="button"
                className="ghost-action"
                title="Per-file stats, sortable"
                onClick={() => setRunsOpen(true)}
              >
                Runs
              </button>
            )}
            {fileCount > 1 && !flags.difference && !flags.autocorrelation && (
              <button
                type="button"
                className={`ghost-action${split ? " active" : ""}`}
                aria-pressed={split}
                title="One panel per file, shared zoom"
                onClick={() => {
                  setSplitZoom(null);
                  setSplit((value) => !value);
                }}
              >
                Split
              </button>
            )}
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
      ) : panels ? (
        <>
          <div className="chart-card chart-fill">
            <Legend
              items={legendItems}
              hidden={hidden}
              onToggle={toggleHidden}
            />
            <div className="split-panels">
              {panels.map((panel) => (
                <div className="split-panel" key={panel.label}>
                  <div className="split-head">
                    <i style={{ background: panel.color }} aria-hidden="true" />
                    <strong>{panel.label}</strong>
                    <span>
                      {panel.latest === null
                        ? "n/a"
                        : formatValue(panel.latest)}{" "}
                      · {panel.rows.toLocaleString()} rows
                      {panel.stride > 1 ? ` · stride ${panel.stride}` : ""}
                    </span>
                  </div>
                  <UPlotChart
                    datasets={panel.datasets}
                    hidden={hidden}
                    timeLabel={timeLabel}
                    markers={markers}
                    hideFooter
                    height={240}
                    zoom={splitZoom}
                    onZoomChange={setSplitZoom}
                    resetKey={`${focus}-${panel.label}`}
                    ref={(handle) => {
                      if (handle) panelRefs.current.set(panel.label, handle);
                      else panelRefs.current.delete(panel.label);
                    }}
                  />
                </div>
              ))}
            </div>
            <div className="chart-foot">
              {(series?.series.some((item) => item.rows > 1000) ?? false) && (
                <span className="chart-presets" role="group" aria-label="Time range">
                {PRESETS.filter((preset) => preset.points === null || series!.series.some((item) => item.rows > preset.points!)).map((preset) => {
                  const active = isSplitPresetActive(preset.points);
                  return (
                    <button
                      key={preset.label}
                      type="button"
                      className={`chart-foot-action${active ? " active" : ""}`}
                      aria-pressed={active}
                      onClick={() => {
                        if (preset.points === null) setSplitZoom(null);
                        else {
                          const range = presetRangeFor(
                            datasets.filter(
                              (dataset) => !hidden.has(dataset.key),
                            ),
                            preset.points,
                          );
                          if (range) setSplitZoom(range);
                        }
                      }}
                    >
                      {preset.label}
                    </button>
                  );
                })}
                </span>
              )}
              {caption && <span>{caption}</span>}
            </div>
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
      ) : (
        <>
          <div className="chart-card chart-fill">
            {flags.autocorrelation && (
              <div className="chart-mode">
                <strong>Autocorrelation</strong>
                <Info text="Mean-centered and normalized to 1 at lag 0. Up to half of each run, capped at 1,000 lag steps." />
              </div>
            )}
            {flags.autocorrelation && !overlaysLoading && series && datasets.length < series.series.length && datasets.length > 0 && (
              <p className="chart-note">{series.series.length - datasets.length} {series.series.length - datasets.length === 1 ? "run" : "runs"} omitted: insufficient data.</p>
            )}
            <Legend
              items={legendItems}
              hidden={hidden}
              onToggle={toggleHidden}
            />
            {flags.autocorrelation && overlaysLoading ? (
              <div className="chart-empty" role="status">Calculating…</div>
            ) : flags.autocorrelation && datasets.length === 0 ? (
              <div className="chart-empty" role="status">
                {overlayError ? "Autocorrelation unavailable." : "Needs two varying values per run."}
              </div>
            ) : (
              <UPlotChart
                datasets={datasets}
                hidden={hidden}
                timeLabel={flags.autocorrelation ? "Lag (steps)" : timeLabel}
                integerX={flags.autocorrelation}
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
      <Modal
        open={dataOpen}
        size="full"
        title={`${focus} — data`}
        subtitle={
          table ? (
            <>
              {table.shown.toLocaleString()} of{" "}
              {table.totalPoints.toLocaleString()} transported points ·{" "}
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
        {table && <SeriesDataTable data={table} />}
      </Modal>
      <Modal
        open={runsOpen}
        size="full"
        title={`${focus} — runs`}
        subtitle={
          summary
            ? `${summary.files.length} file${summary.files.length === 1 ? "" : "s"} · combined pinned · click a header to sort`
            : undefined
        }
        onClose={() => setRunsOpen(false)}
      >
        {summary && (
          <RunsTable files={summary.files} combined={summary.combined} />
        )}
      </Modal>
    </section>
  );
}
