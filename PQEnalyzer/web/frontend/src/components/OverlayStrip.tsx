import type { Dispatch, SetStateAction } from "react";
import { formatValue, type OverlayFlags, type OverlayItem } from "../api";
import { OVERLAY_DEFS } from "./RailBlocks";

export type OverlayPresetId =
  | "off"
  | "reference"
  | "spread"
  | "trend"
  | "equilibrate"
  | "correlate";

/** One-click overlay combos; difference stays manual (it hides raw data). */
export const OVERLAY_PRESETS: {
  id: OverlayPresetId;
  label: string;
  title: string;
  flags: OverlayFlags;
}[] = [
  {
    id: "off",
    label: "Off",
    title: "All overlays off",
    flags: {
      mean: false,
      median: false,
      cummulative_average: false,
      self_correlation_mean: false,
      difference: false,
      running_average: false,
    },
  },
  {
    id: "reference",
    label: "Reference",
    title: "Combined mean as reference",
    flags: {
      mean: true,
      median: false,
      cummulative_average: false,
      self_correlation_mean: false,
      difference: false,
      running_average: false,
    },
  },
  {
    id: "spread",
    label: "Spread",
    title: "Mean + median skew check",
    flags: {
      mean: true,
      median: true,
      cummulative_average: false,
      self_correlation_mean: false,
      difference: false,
      running_average: false,
    },
  },
  {
    id: "trend",
    label: "Trend",
    title: "Running average for drift hunting",
    flags: {
      mean: false,
      median: false,
      cummulative_average: false,
      self_correlation_mean: false,
      difference: false,
      running_average: true,
    },
  },
  {
    id: "equilibrate",
    label: "Equilibrate",
    title: "Cumulative average for convergence check",
    flags: {
      mean: false,
      median: false,
      cummulative_average: true,
      self_correlation_mean: false,
      difference: false,
      running_average: false,
    },
  },
  {
    id: "correlate",
    label: "Correlate",
    title: "Self-correlation mean",
    flags: {
      mean: false,
      median: false,
      cummulative_average: false,
      self_correlation_mean: true,
      difference: false,
      running_average: false,
    },
  },
];

/** Which preset (if any) the current flags match exactly. */
export function matchingPreset(flags: OverlayFlags): OverlayPresetId | null {
  const found = OVERLAY_PRESETS.find((preset) =>
    (Object.keys(preset.flags) as (keyof OverlayFlags)[]).every(
      (key) => preset.flags[key] === flags[key],
    ),
  );
  return found?.id ?? null;
}

function latestValue(overlays: OverlayItem[], key: string): number | null {
  const overlay = overlays.find((item) => item.key === key);
  if (!overlay) return null;
  for (let i = overlay.values.length - 1; i >= 0; i -= 1) {
    const value = overlay.values[i];
    if (typeof value === "number") return value;
  }
  return null;
}

/**
 * Overlays as first-class citizens: always-visible toggle chips with
 * live latest values plus one-click presets. The tools panel keeps the
 * advanced controls (smoothing window, bins); this strip is the daily
 * driver.
 */
export function OverlayStrip({
  flags,
  setFlags,
  overlays,
  fileCount,
}: {
  flags: OverlayFlags;
  setFlags: Dispatch<SetStateAction<OverlayFlags>>;
  overlays: OverlayItem[];
  fileCount: number;
}) {
  const activePreset = matchingPreset(flags);
  return (
    <div className="overlay-strip" role="group" aria-label="Overlays">
      <span className="strip-label" aria-hidden="true">
        Overlays
      </span>
      {OVERLAY_DEFS.map((def) => {
        const on = flags[def.key];
        const disabled =
          (def.key === "difference" && fileCount !== 2) ||
          (def.key !== "difference" && flags.difference);
        const latest = on ? latestValue(overlays, def.key) : null;
        return (
          <button
            key={def.key}
            type="button"
            className={`legend-chip${on ? "" : " off"}`}
            aria-pressed={on}
            disabled={disabled}
            title={`${def.label} overlay (${def.shortcut})`}
            onClick={() =>
              setFlags((current) => ({ ...current, [def.key]: !current[def.key] }))
            }
          >
            <span>{def.label}</span>
            {on && (
              <strong>{latest === null ? "…" : formatValue(latest)}</strong>
            )}
          </button>
        );
      })}
      <i className="strip-sep" aria-hidden="true" />
      {OVERLAY_PRESETS.map((preset) => (
        <button
          key={preset.id}
          type="button"
          className={`chart-foot-action${activePreset === preset.id ? " active" : ""}`}
          aria-pressed={activePreset === preset.id}
          title={preset.title}
          onClick={() => setFlags({ ...preset.flags })}
        >
          {preset.label}
        </button>
      ))}
    </div>
  );
}
