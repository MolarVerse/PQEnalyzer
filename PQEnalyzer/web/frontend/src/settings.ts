import type { OverlayFlags } from "./api";

/**
 * Persisted UI choices (analysis and dashboard sort).
 * Browser localStorage: survives server restarts and reloads, needs no
 * backend, stays per-user. Shape is versioned; anything unknown or
 * malformed falls back to built-in defaults.
 */
export interface WebSettings {
  version: 1;
  overlays: Partial<OverlayFlags>;
  sortMode: string;
}

export const SETTINGS_KEY = "pqenalyzer.web.settings.v1";

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export function defaultSettings(): WebSettings {
  return {
    version: 1,
    overlays: { mean: true },
    sortMode: "name",
  };
}

const KNOWN_OVERLAYS: (keyof OverlayFlags)[] = [
  "mean",
  "median",
  "cummulative_average",
  "autocorrelation",
  "running_average",
];

/** Keep known boolean entries; unknown keys are ignored, not fatal. */
function cleanOverlays(value: unknown): Partial<OverlayFlags> {
  if (typeof value !== "object" || value === null) return {};
  const cleaned: Partial<OverlayFlags> = {};
  for (const key of KNOWN_OVERLAYS) {
    const entry = (value as Record<string, unknown>)[key];
    if (typeof entry === "boolean") {
      (cleaned as Record<string, boolean>)[key] = entry;
    }
  }
  return cleaned;
}

/** Read stored settings; unknown/missing storage yields defaults. */
export function loadSettings(storage?: StorageLike | null): WebSettings {
  const fallback = defaultSettings();
  if (!storage) return fallback;
  let raw: string | null = null;
  try {
    raw = storage.getItem(SETTINGS_KEY);
  } catch {
    return fallback;
  }
  if (!raw) return fallback;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return fallback;
  }
  if (typeof parsed !== "object" || parsed === null) return fallback;
  const record = parsed as Record<string, unknown>;
  if (record.version !== 1) return fallback;
  const settings = defaultSettings();
  {
    const rest = cleanOverlays(record.overlays);
    settings.overlays = { ...settings.overlays, ...rest };
    const old = (record.overlays as Record<string, unknown> | undefined)
      ?.self_correlation_mean;
    if (typeof old === "boolean" && !("autocorrelation" in rest)) {
      settings.overlays.autocorrelation = old;
    }
  }
  if (settings.overlays.autocorrelation) {
    settings.overlays = { autocorrelation: true };
  }
  if (record.sortMode === "name" || record.sortMode === "drift") {
    settings.sortMode = record.sortMode;
  }
  return settings;
}

/** Persist settings; storage errors (private mode) stay silent. */
export function saveSettings(storage: StorageLike | null, settings: WebSettings): void {
  if (!storage) return;
  try {
    storage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    /* private mode: preferences simply don't persist */
  }
}

/** Browser storage handle (null outside a DOM context). */
export function browserStorage(): StorageLike | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}
