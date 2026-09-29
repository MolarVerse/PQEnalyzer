import { useCallback, useEffect, useRef, useState } from "react";
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
  const [overlaysLoading, setOverlaysLoading] = useState(false);
  const [seriesError, setSeriesError] = useState<string | null>(null);
  const [histogramError, setHistogramError] = useState<string | null>(null);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [loadedRevision, setLoadedRevision] = useState(0);
  const seriesRequest = useRef(0);

  const loadParameter = useCallback(
    async (name: string) => {
      const request = ++seriesRequest.current;
      setSeriesError(null);
      setSeriesLoading(true);
      try {
        const [loadedSeries, loadedSummary] = await Promise.all([
          fetchSeries(name),
          fetchSummary(name),
        ]);
        if (request !== seriesRequest.current) return;
        setSeries(loadedSeries);
        setSummary(loadedSummary);
        setLoadedRevision((current) => current + 1);
      } catch (error) {
        if (request === seriesRequest.current) {
          setSeriesError(error instanceof Error ? error.message : String(error));
        }
      } finally {
        if (request === seriesRequest.current) setSeriesLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (focus) {
      setSeriesError(null);
      setHistogramError(null);
      setSeries(null);
      setSummary(null);
      setOverlays([]);
      setHistogram(null);
      void loadParameter(focus);
    } else {
      seriesRequest.current += 1;
      setSeries(null);
      setSummary(null);
    }
  }, [focus, loadParameter]);

  useEffect(() => {
    let active = true;
    setOverlays([]);
    setOverlayError(null);
    if (!focus || series?.parameter !== focus || !Object.values(flags).some(Boolean)) {
      setOverlaysLoading(false);
      return () => { active = false; };
    }
    setOverlaysLoading(true);
    fetchOverlays(focus, flags, windowSize)
      .then((loaded) => {
        if (active) {
          setOverlays(loaded.overlays);
          setOverlaysLoading(false);
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setOverlayError(error instanceof Error ? error.message : String(error));
          setOverlaysLoading(false);
        }
      });
    return () => { active = false; };
  }, [focus, series?.parameter, flags, windowSize, loadedRevision]);

  useEffect(() => {
    if (!focus || mode !== "histogram" || series?.parameter !== focus) return;
    let active = true;
    setHistogram(null);
    setHistogramError(null);
    fetchHistogram(focus, bins)
      .then((loaded) => { if (active) setHistogram(loaded); })
      .catch((error: unknown) => {
        if (active) setHistogramError(error instanceof Error ? error.message : String(error));
      });
    return () => { active = false; };
  }, [focus, mode, bins, loadedRevision, series?.parameter]);

  return {
    series,
    overlays,
    overlaysLoading,
    histogram,
    summary,
    overlayError,
    error: focus ? seriesError ?? (mode === "histogram" ? histogramError : null) : null,
    seriesLoading,
    loadParameter,
  };
}
