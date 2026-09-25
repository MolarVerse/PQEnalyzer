import { useCallback, useEffect, useState } from "react";
import {
  fetchHistogram,
  fetchOverlays,
  fetchSeries,
  fetchSummary,
  type HistogramResponse,
  type OverlayFlags,
  type OverlayItem,
  type SeriesResponse,
  type SummaryResponse,
} from "../api";
import type { Mode } from "../mode";

/**
 * Parameter-level data for the focused parameter: series + overlays +
 * summary, and the histogram when in histogram mode. Session-level data
 * (files, parameters, summaries) lives in useSession.
 */
export function useParameterData(
  focus: string | null,
  flags: OverlayFlags,
  windowSize: string,
  bins: string,
  mode: Mode,
) {
  const [series, setSeries] = useState<SeriesResponse | null>(null);
  const [overlays, setOverlays] = useState<OverlayItem[]>([]);
  const [histogram, setHistogram] = useState<HistogramResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [overlayError, setOverlayError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [seriesLoading, setSeriesLoading] = useState(false);

  const loadParameter = useCallback(
    async (name: string) => {
      setError(null);
      setOverlayError(null);
      setSeriesLoading(true);
      try {
        const [loadedSeries, loadedSummary] = await Promise.all([
          fetchSeries(name),
          fetchSummary(name),
        ]);
        setSeries(loadedSeries);
        setSummary(loadedSummary);
        if (Object.values(flags).some(Boolean)) {
          try {
            const loaded = await fetchOverlays(name, flags, windowSize);
            setOverlays(loaded.overlays);
          } catch (error) {
            setOverlays([]);
            setOverlayError(error instanceof Error ? error.message : String(error));
          }
        } else {
          setOverlays([]);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : String(error));
      } finally {
        setSeriesLoading(false);
      }
    },
    [flags, windowSize],
  );

  useEffect(() => {
    if (focus) void loadParameter(focus);
  }, [focus, loadParameter]);

  useEffect(() => {
    if (!focus || mode !== "histogram") return;
    fetchHistogram(focus, Number(bins) || 48)
      .then(setHistogram)
      .catch((error: unknown) =>
        setError(error instanceof Error ? error.message : String(error)),
      );
  }, [focus, mode, bins]);

  return {
    series,
    overlays,
    histogram,
    summary,
    overlayError,
    error,
    seriesLoading,
    loadParameter,
  };
}
