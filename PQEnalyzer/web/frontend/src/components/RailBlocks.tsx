import { Field, Toggle } from "@molarverse/pq-design";
import type { Dispatch, SetStateAction } from "react";
import { histogramBinSelection, type OverlayFlags } from "../api";

export interface SharedControls {
  flags: OverlayFlags;
  setFlags: Dispatch<SetStateAction<OverlayFlags>>;
}

export const OVERLAY_DEFS: {
  key: keyof OverlayFlags;
  label: string;
  shortcut: string;
  description: string;
}[] = [
  { key: "mean", label: "Mean", shortcut: "m", description: "One guide for all data" },
  { key: "median", label: "Median", shortcut: "n", description: "One guide for all data" },
  { key: "cumulative_average", label: "Cumulative average", shortcut: "c", description: "Continues across files" },
  { key: "running_average", label: "Running average", shortcut: "a", description: "Smooths the combined sequence" },
  { key: "autocorrelation", label: "Autocorrelation", shortcut: "s", description: "Switch chart to lag correlation" },
];

export const NO_OVERLAYS: OverlayFlags = {
  mean: false,
  median: false,
  cumulative_average: false,
  running_average: false,
  autocorrelation: false,
};

export function toggleOverlay(current: OverlayFlags, key: keyof OverlayFlags): OverlayFlags {
  if (key === "autocorrelation") {
    return { ...NO_OVERLAYS, [key]: !current[key] };
  }
  return { ...current, autocorrelation: false, [key]: !current[key] };
}

const ANALYSIS_GROUPS = [
  { title: "Reference", keys: ["mean", "median"] },
  { title: "Trend", keys: ["cumulative_average", "running_average"] },
  { title: "Correlation", keys: ["autocorrelation"] },
] as const;

export function AnalysisPicker({
  flags,
  setFlags,
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
            return (
              <button
                key={key}
                type="button"
                className="analysis-option"
                aria-pressed={flags[key]}
                title={def.description}
                onClick={() => setFlags((current) => toggleOverlay(current, key))}
              >
                <span className="analysis-check" aria-hidden="true">{flags[key] ? "✓" : ""}</span>
                <span className="analysis-option-label">{def.label}</span>
              </button>
            );
          })}
          {group.title === "Trend" && flags.running_average && (
            <div className="analysis-window">
              <Field
                label="Window"
                unit="steps"
                info="Auto uses about 5% of the combined sequence and keeps at least two plotted points."
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
      <Field label="Bins" info="Auto chooses a bin width from all values. Set a number to override it.">
        <input
          type="number"
          min={2}
          max={200}
          step={1}
          value={bins}
          placeholder="auto"
          onChange={(event) => setBins(event.target.value)}
          onBlur={() => setBins(histogramBinSelection(bins) === "auto" ? "" : histogramBinSelection(bins))}
        />
      </Field>
      {bins && <button type="button" className="use-auto" onClick={() => setBins("")}>Use auto</button>}
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
