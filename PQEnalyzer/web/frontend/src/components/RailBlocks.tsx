import { Field, Info, Toggle } from "@molarverse/pq-design";
import type { Dispatch, SetStateAction } from "react";
import type { OverlayFlags, StatBlock } from "../api";

export interface SharedControls {
  flags: OverlayFlags;
  setFlags: Dispatch<SetStateAction<OverlayFlags>>;
  fileCount: number;
}

export const OVERLAY_DEFS: {
  key: keyof OverlayFlags;
  label: string;
  shortcut: string;
}[] = [
  { key: "mean", label: "Mean", shortcut: "m" },
  { key: "median", label: "Median", shortcut: "n" },
  { key: "cummulative_average", label: "Cumulative average", shortcut: "c" },
  { key: "self_correlation_mean", label: "Self-correlation mean", shortcut: "s" },
  { key: "difference", label: "Difference (1 − 2)", shortcut: "x" },
  { key: "running_average", label: "Running average", shortcut: "a" },
];

export function OverlaysBlock({
  flags,
  setFlags,
  fileCount,
  windowSize,
  setWindowSize,
  maxWindow,
}: SharedControls & {
  windowSize: string;
  setWindowSize: (value: string) => void;
  maxWindow: number;
}) {
  const sliderValue = Math.min(
    Math.max(Number(windowSize) || 1, 1),
    Math.max(maxWindow, 1),
  );
  return (
    <section className="setup-section">
      <h2 className="section-title">
        Overlays
        <Info text="Derived curves use the same math as the desktop GUI and TUI. Keyboard: m mean · n median · c cumulative · s self-correlation · x difference · a running average." />
      </h2>
      <div className="toggle-group">
        {OVERLAY_DEFS.map((def) => (
          <Toggle
            key={def.key}
            label={def.label}
            checked={flags[def.key]}
            disabled={
              (def.key === "difference" && fileCount !== 2) ||
              (def.key !== "difference" && flags.difference)
            }
            onChange={(value) =>
              setFlags((current) => ({ ...current, [def.key]: value }))
            }
          />
        ))}
      </div>
      {flags.running_average && (
        <>
          <Field
            label="Running-average window"
            unit="steps"
            info="Clamped to the series length."
          >
            <input
              type="number"
              min={1}
              max={maxWindow}
              value={windowSize}
              onChange={(event) => setWindowSize(event.target.value)}
            />
          </Field>
          <label className="smooth-slider">
            <span>Smooth</span>
            <input
              type="range"
              min={1}
              max={Math.max(maxWindow, 1)}
              step={1}
              value={sliderValue}
              aria-label="Smoothing window in steps"
              onChange={(event) => setWindowSize(event.target.value)}
            />
            <output>{sliderValue.toLocaleString()}</output>
          </label>
        </>
      )}
    </section>
  );
}

export function HistogramBlock({
  flags,
  setFlags,
  bins,
  setBins,
  showKde,
  setShowKde,
  kdeAvailable,
}: Pick<SharedControls, "flags" | "setFlags"> & {
  bins: string;
  setBins: (value: string) => void;
  showKde: boolean;
  setShowKde: (value: boolean) => void;
  kdeAvailable: boolean;
}) {
  return (
    <section className="setup-section">
      <h2 className="section-title">Histogram</h2>
      <Field label="Bins" info="Shared edges across files.">
        <input
          type="number"
          min={8}
          max={200}
          value={bins}
          onChange={(event) => setBins(event.target.value)}
        />
      </Field>
      <div className="toggle-group">
        <Toggle
          label="Mean guide"
          checked={flags.mean}
          onChange={(value) =>
            setFlags((current) => ({ ...current, mean: value }))
          }
        />
        <Toggle
          label="Median guide"
          checked={flags.median}
          onChange={(value) =>
            setFlags((current) => ({ ...current, median: value }))
          }
        />
        <Toggle
          label="KDE estimate"
          info="Gaussian kernel density estimate of the combined values, scaled to bin counts."
          checked={showKde}
          disabled={!kdeAvailable}
          onChange={setShowKde}
        />
      </div>
    </section>
  );
}

export interface SoftBounds {
  min: string;
  max: string;
}

/** Expand-only y-axis bounds (Grafana-style soft min/max; blank = auto). */
export function YAxisBlock({
  bounds,
  setBounds,
}: {
  bounds: SoftBounds;
  setBounds: Dispatch<SetStateAction<SoftBounds>>;
}) {
  return (
    <section className="setup-section">
      <h2 className="section-title">
        Y-axis
        <Info text="Soft bounds widen the axis but never clip data. Blank means auto." />
      </h2>
      <div className="bounds-row">
        <Field label="Soft min">
          <input
            type="text"
            inputMode="decimal"
            placeholder="auto"
            aria-label="Soft y-axis minimum"
            value={bounds.min}
            onChange={(event) =>
              setBounds((current) => ({ ...current, min: event.target.value }))
            }
          />
        </Field>
        <Field label="Soft max">
          <input
            type="text"
            inputMode="decimal"
            placeholder="auto"
            aria-label="Soft y-axis maximum"
            value={bounds.max}
            onChange={(event) =>
              setBounds((current) => ({ ...current, max: event.target.value }))
            }
          />
        </Field>
      </div>
    </section>
  );
}

export function AnalysisBlock({
  stats,
  showMarker,
  setShowMarker,
}: {
  stats: StatBlock | null;
  showMarker: boolean;
  setShowMarker: (value: boolean) => void;
}) {
  const analysis = stats?.analysis;
  const equilibrated = analysis?.equilibrated ?? null;
  const discarded = analysis?.discarded_fraction ?? null;
  return (
    <section className="setup-section">
      <h2 className="section-title">
        Analysis
        <Info text="Correlated error bars (Flyvbjerg–Petersen blocking, Geyer truncation) and MSER equilibration. Naive std over root-n underestimates uncertainty for simulation data." />
      </h2>
      <dl className="analysis-list">
        <div>
          <dt>Correlation time</dt>
          <dd>
            {analysis?.correlation_time != null
              ? `${Math.round(analysis.correlation_time)} steps`
              : "n/a"}
          </dd>
        </div>
        <div>
          <dt>Inefficiency</dt>
          <dd>
            {analysis?.inefficiency != null
              ? Math.round(analysis.inefficiency).toLocaleString()
              : "n/a"}
          </dd>
        </div>
        <div>
          <dt>Effective N</dt>
          <dd>
            {analysis?.n_effective != null
              ? Math.round(analysis.n_effective).toLocaleString()
              : "n/a"}
          </dd>
        </div>
        <div>
          <dt>Equilibrated</dt>
          <dd>
            {equilibrated === null ? (
              "n/a"
            ) : (
              <span className={`pq-tag ${equilibrated ? "ok" : "missing"}`}>
                <span className="pq-tag-value">
                  {equilibrated ? "yes" : "no"}
                  {discarded !== null
                    ? ` · ${Math.round(discarded * 100)}% cut`
                    : ""}
                </span>
              </span>
            )}
          </dd>
        </div>
      </dl>
      <div className="toggle-group">
        <Toggle
          label="Equilibration marker"
          info="Shows the MSER equilibration point on the chart."
          checked={showMarker}
          disabled={analysis?.equil_time == null}
          onChange={setShowMarker}
        />
      </div>
    </section>
  );
}
