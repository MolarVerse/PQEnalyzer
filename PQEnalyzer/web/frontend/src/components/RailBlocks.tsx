import { Field, Toggle } from "@molarverse/pq-design";
import type { Dispatch, SetStateAction } from "react";
import type { OverlayFlags } from "../api";

export interface SharedControls {
  flags: OverlayFlags;
  setFlags: Dispatch<SetStateAction<OverlayFlags>>;
  fileCount: number;
  canDifference: boolean;
}

export const OVERLAY_DEFS: {
  key: keyof OverlayFlags;
  label: string;
  shortcut: string;
  description: string;
}[] = [
  { key: "mean", label: "Mean", shortcut: "m", description: "One guide across all runs" },
  { key: "median", label: "Median", shortcut: "n", description: "One guide across all runs" },
  { key: "cummulative_average", label: "Cumulative average", shortcut: "c", description: "Restarts at each run" },
  { key: "running_average", label: "Running average", shortcut: "a", description: "Smooths each run separately" },
  { key: "autocorrelation", label: "Autocorrelation", shortcut: "s", description: "Switch chart to lag correlation" },
  { key: "difference", label: "Difference (1 − 2)", shortcut: "x", description: "Subtracts run 2 on shared steps" },
];

export const NO_OVERLAYS: OverlayFlags = {
  mean: false,
  median: false,
  cummulative_average: false,
  running_average: false,
  autocorrelation: false,
  difference: false,
};

export function toggleOverlay(current: OverlayFlags, key: keyof OverlayFlags): OverlayFlags {
  if (key === "difference" || key === "autocorrelation") {
    return { ...NO_OVERLAYS, [key]: !current[key] };
  }
  return { ...current, difference: false, autocorrelation: false, [key]: !current[key] };
}

const ANALYSIS_GROUPS = [
  { title: "Reference", keys: ["mean", "median"] },
  { title: "Trend per run", keys: ["cummulative_average", "running_average"] },
  { title: "Correlation", keys: ["autocorrelation"] },
  { title: "Compare runs", keys: ["difference"] },
] as const;

export function AnalysisPicker({
  flags,
  setFlags,
  fileCount,
  canDifference,
  windowSize,
  setWindowSize,
  maxWindow,
}: SharedControls & {
  windowSize: string;
  setWindowSize: (value: string) => void;
  maxWindow: number;
}) {
  return (
    <section className="analysis-picker">
      {ANALYSIS_GROUPS.map((group) => (
        <div className="analysis-group" role="group" aria-label={group.title} key={group.title}>
          <h2>{group.title}</h2>
          {group.keys.map((key) => {
            const def = OVERLAY_DEFS.find((item) => item.key === key)!;
            const unavailable = key === "difference" && (!canDifference || fileCount !== 2);
            return (
              <button
                key={key}
                type="button"
                className="analysis-option"
                aria-pressed={flags[key]}
                title={def.description}
                disabled={unavailable}
                onClick={() => setFlags((current) => toggleOverlay(current, key))}
              >
                <span className="analysis-check" aria-hidden="true">{flags[key] ? "✓" : ""}</span>
                <span className="analysis-option-label">{def.label}</span>
              </button>
            );
          })}
          {group.title === "Trend per run" && flags.running_average && (
            <div className="analysis-window">
              <Field
                label="Window"
                unit="steps"
                info="Auto uses about 5% of each run and keeps at least two plotted points."
              >
                <input
                  type="number"
                  min={1}
                  max={maxWindow}
                  value={windowSize}
                  placeholder="auto"
                  onChange={(event) => setWindowSize(event.target.value)}
                />
              </Field>
              {windowSize && (
                <button type="button" onClick={() => setWindowSize("")}>Use auto</button>
              )}
            </div>
          )}
          {group.title === "Compare runs" && !canDifference && (
            <p className="analysis-help">Needs 2 runs with shared steps.</p>
          )}
        </div>
      ))}
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
