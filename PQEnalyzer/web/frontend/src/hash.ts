/*
 * URL hash state for PQEnalyzer Web (LOCAL-ONLY preview).
 * The shareable link carries display mode (m) and focused parameter (p).
 */

export type HashMode = "series" | "histogram";

export interface HashState {
  parameter: string | null;
  mode: HashMode | null;
}

/** Parse a location-hash string (with or without the leading #). */
export function parseHash(hash: string): HashState {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const mode = params.get("m");
  // Legacy links used v=series|histogram|dashboard instead of m.
  const legacy = params.get("v");
  return {
    parameter: params.get("p"),
    mode:
      mode === "series" || mode === "histogram" ? mode
      : legacy === "histogram" ? "histogram"
      : legacy === "series" ? "series"
      : null,
  };
}

/** Read the current location hash. */
export function hashState(): HashState {
  return parseHash(window.location.hash);
}

/** Mutate the current location hash in place. */
export function writeHash(mutate: (params: URLSearchParams) => void): void {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  mutate(params);
  window.location.hash = params.toString();
}
