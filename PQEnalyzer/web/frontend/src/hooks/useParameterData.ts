import { useEffect, useState } from "react";
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
 * Load the selected chart directly; each endpoint can succeed on its own.
 */
export function useParameterData(
  focus: string | null,
  flags: OverlayFlags,
  windowSize: string,
  bins: string,
  mode: Mode,
  generation: number,
) {
  const [series, setSeries] = useState<SeriesResponse | null>(null);
  const [overlays, setOverlays] = useState<OverlayItem[]>([]);
  const [histogram, setHistogram] = useState<HistogramResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [overlayError, setOverlayError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [overlaysLoading, setOverlaysLoading] = useState(false);
  const [seriesError, setSeriesError] = useState<string | null>(null);
  const [histogramError, setHistogramError] = useState<string | null>(null);
  const [seriesLoading, setSeriesLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setSummary(null);
    setSummaryError(null);
    if (focus) {
      fetchSummary(focus)
        .then((loaded) => { if (active) setSummary(loaded); })
        .catch((error: unknown) => {
          if (active) setSummaryError(error instanceof Error ? error.message : String(error));
        });
    }
    return () => { active = false; };
  }, [focus, generation]);

  useEffect(() => {
    let active = true;
    setSeries(null);
    setSeriesError(null);
    if (!focus || mode !== "series") {
      setSeriesLoading(false);
      return () => { active = false; };
    }
    setSeriesLoading(true);
    fetchSeries(focus)
      .then((loaded) => { if (active) setSeries(loaded); })
      .catch((error: unknown) => {
        if (active) setSeriesError(error instanceof Error ? error.message : String(error));
      })
      .finally(() => { if (active) setSeriesLoading(false); });
    return () => { active = false; };
  }, [focus, mode, generation]);

  useEffect(() => {
    let active = true;
    setOverlays([]);
    setOverlayError(null);
    if (
      !focus || mode !== "series" || series?.parameter !== focus ||
      !Object.values(flags).some(Boolean)
    ) {
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
  }, [focus, mode, series?.parameter, flags, windowSize, generation]);

  useEffect(() => {
    let active = true;
    setHistogram(null);
    setHistogramError(null);
    if (focus && mode === "histogram") {
      fetchHistogram(focus, bins)
        .then((loaded) => { if (active) setHistogram(loaded); })
        .catch((error: unknown) => {
          if (active) setHistogramError(error instanceof Error ? error.message : String(error));
        });
    }
    return () => { active = false; };
  }, [focus, mode, bins, generation]);

  return {
    series: series?.parameter === focus ? series : null,
    overlays,
    overlaysLoading,
    histogram: histogram?.parameter === focus ? histogram : null,
    summary: summary?.parameter === focus ? summary : null,
    summaryError,
    overlayError,
    error: focus ? (mode === "series" ? seriesError : histogramError) : null,
    seriesLoading,
  };
}
