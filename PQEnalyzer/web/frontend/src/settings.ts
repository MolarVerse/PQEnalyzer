import type { OverlayFlags } from "./api";

/**
 * Persisted UI taste (overlay defaults, soft bounds, dashboard sort).
 * Browser localStorage: survives server restarts and reloads, needs no
 * backend, stays per-user. Shape is versioned; anything unknown or
 * malformed falls back to built-in defaults. `difference` is never
 * restored — it hides raw data, so it stays an explicit per-session act.
 */
export interface WebSettings {
  version: 1;
  overlays: Partial<OverlayFlags>;
  softBounds: { min: string; max: string };
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
    softBounds: { min: "", max: "" },
    sortMode: "name",
  };
}

const KNOWN_OVERLAYS: (keyof OverlayFlags)[] = [
  "mean",
  "median",
  "cummulative_average",
  "self_correlation_mean",
  "difference",
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
    const { difference: _dropped, ...rest } = cleanOverlays(record.overlays);
    void _dropped;
    settings.overlays = { ...settings.overlays, ...rest };
  }
  const bounds = record.softBounds as { min?: unknown; max?: unknown } | undefined;
  if (bounds && typeof bounds.min === "string" && typeof bounds.max === "string") {
    settings.softBounds = { min: bounds.min, max: bounds.max };
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
