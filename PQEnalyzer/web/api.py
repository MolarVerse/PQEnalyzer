"""
JSON data layer for the PQEnalyzer web front end (LOCAL-ONLY preview).

Every number here flows through the shared code: ``readers`` for parsing,
``energy_access`` for series/units, ``plots.features`` for overlay math, and
``plots.labels`` for file labels. The web layer only shapes results into JSON:
downsampling for transport, NaN sanitising (``null`` breaks SVG paths into
honest gaps), and per-file histogram binning on shared edges.
"""

import math
import json
import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from ..energy_access import (
    available_parameters,
    axis_label,
    concatenate_series,
    parameter_kind,
    parameter_unit_for_energies,
    series,
    simulation_time,
)
from ..plots.features import (
    iter_histogram_guides,
    iter_time_series_overlays,
)
from ..plots.labels import parameter_label, unique_path_labels
from ..plots.options import PlotOptions
from ..statistics import Statistic

MAX_POINTS = 4000
SPARK_POINTS = 120
HISTOGRAM_BINS_DEFAULT = 48
#: Seconds between file-watcher mtime scans.
WATCH_INTERVAL = 0.5
#: SSE reconnect hint (ms) so a restarted server resumes live updates.
SSE_RETRY_MS = 2000


def format_sse_event(event, data):
    """
    Render one SSE event. Payloads are compact JSON (no newlines inside).
    """
    return f"event: {event}\ndata: {data}\n\n"


class WebState:
    """
    Mutable server state: the reader plus a file snapshot for staleness.

    FastAPI serves requests sequentially on a single worker; the lock keeps
    refresh-while-reading safe if the server is ever run threaded.
    """

    def __init__(self, reader):
        """
        Snapshot the freshly read files.
        """
        self.reader = reader
        self.filenames = list(reader.filenames)
        self.labels = unique_path_labels(self.filenames)
        self.lock = threading.Lock()
        # Persistent pool: per-request pools cost more in thread startup
        # than the numpy work they parallelize.
        self.pool = ThreadPoolExecutor(max_workers=4)
        # Dashboard payload cache: file contents are immutable between
        # refreshes. Warmed eagerly at startup and on every refresh so the
        # first dashboard load never stampedes the thread pool.
        self._summaries_cache = {}
        self.snapshot = _snapshot_files(self.filenames)
        self._summaries_cache[_snapshot_key(self.snapshot)] = (
            self._compute_summaries(list(reader.energies)))
        # Push staleness: lazy watcher thread plus one bounded queue per
        # SSE subscriber (slow clients drop beats; the next change
        # re-notifies, and every refresh clears explicitly).
        self._subscribers = []
        self._subs_lock = threading.Lock()
        self._watcher_started = False

    def status(self):
        """
        Return per-file rows/mtime plus whether files changed on disk.
        """
        with self.lock:
            current = _snapshot_files(self.filenames)
            rows = [_row_count(energy) for energy in self.reader.energies]
        files = []
        stale = False
        for filename, label, row in zip(self.filenames, self.labels, rows):
            changed = current.get(filename) != self.snapshot.get(filename)
            stale = stale or changed
            files.append({
                "label": label,
                "path": filename,
                "rows": row,
                "stale": changed,
            })
        return {"files": files, "stale": stale}

    def refresh(self):
        """
        Re-read all files and return the fresh status.
        """
        with self.lock:
            self.reader.read()
            self.snapshot = _snapshot_files(self.filenames)
            energies = list(self.reader.energies)
        self._summaries_cache = {
            _snapshot_key(self.snapshot): self._compute_summaries(energies),
        }
        return self.status()

    def subscribe(self):
        """
        Register a bounded queue for staleness pushes. Starts the watcher
        thread lazily so states without SSE clients cost nothing.
        """
        subscriber = queue.Queue(maxsize=8)
        with self._subs_lock:
            self._subscribers.append(subscriber)
            if not self._watcher_started:
                self._watcher_started = True
                thread = threading.Thread(
                    target=self._watch_files,
                    name="pqenalyzer-watch",
                    daemon=True,
                )
                thread.start()
        return subscriber

    def unsubscribe(self, subscriber):
        """
        Drop a subscriber queue (client gone).
        """
        with self._subs_lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    def _watch_files(self):
        """
        Poll mtimes and push one `stale` event per fresh→stale transition.
        """
        was_stale = False
        while True:
            time.sleep(WATCH_INTERVAL)
            with self.lock:
                baseline = self.snapshot
            current = _snapshot_files(self.filenames)
            stale = any(
                current.get(filename) != baseline.get(filename)
                for filename in self.filenames
            )
            if stale and not was_stale:
                payload = format_sse_event(
                    "stale", json.dumps({"stale": True}))
                with self._subs_lock:
                    subscribers = list(self._subscribers)
                for subscriber in subscribers:
                    try:
                        subscriber.put_nowait(payload)
                    except queue.Full:
                        pass
            was_stale = stale

    def events(self, heartbeat=15.0):
        """
        SSE stream for one client: reconnect hint, a `hello` carrying the
        current status, then `stale` pushes and `: ping` heartbeats (which
        also bound how long a dead client can linger).
        """
        subscriber = self.subscribe()
        try:
            yield f"retry: {SSE_RETRY_MS}\n\n"
            yield format_sse_event("hello", json.dumps(self.status()))
            while True:
                try:
                    yield subscriber.get(timeout=heartbeat)
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(subscriber)

    def meta(self):
        """
        Return files, reader kind, and axis labelling for the session.
        """
        with self.lock:
            energies = list(self.reader.energies)
            reader_kind = type(self.reader).__name__
        time_label = axis_label(energies[0]) if energies else "Simulation Time"
        status = self.status()
        return {
            "reader": reader_kind,
            "time_label": time_label,
            "files": status["files"],
            "stale": status["stale"],
        }

    def parameters(self):
        """
        Return every plottable parameter with unit and coverage.
        """
        with self.lock:
            energies = list(self.reader.energies)
        names = available_parameters(energies, include_time=False)
        items = []
        for name in names:
            matching = _matching_indices(energies, name)
            try:
                unit = parameter_unit_for_energies(energies, name)
            except ValueError:
                unit = ""
            rows = sum(_row_count(energies[index]) for index in matching)
            items.append({
                "name": name,
                "unit": unit,
                "label": parameter_label(name, unit),
                "files": len(matching),
                "rows": rows,
                "kind": _kind_of(energies, name),
            })
        return {"parameters": items}

    def series(self, parameter, max_points=MAX_POINTS):
        """
        Return downsampled raw series for every file exposing a parameter.
        """
        with self.lock:
            energies = list(self.reader.energies)
        matching = _matching_indices(energies, parameter)
        if not matching:
            raise ValueError(
                f"Parameter {parameter} is not present in any input file.")
        unit = parameter_unit_for_energies(energies, parameter)
        items = []
        for index in matching:
            energy = energies[index]
            raw_time = np.asarray(simulation_time(energy), dtype=float)
            raw_values = np.asarray(
                series(energy, parameter).values, dtype=float)
            time, values, stride = _downsample(
                raw_time, raw_values, max_points)
            items.append({
                "label": self.labels[index],
                "rows": int(raw_values.size),
                "stride": stride,
                "downsampled": stride > 1,
                "min": _finite_min(raw_values),
                "max": _finite_max(raw_values),
                "time": _json_list(time),
                "values": _json_list(values),
            })
        time_unit = _time_unit(energies)
        return {
            "parameter": parameter,
            "unit": unit,
            "label": parameter_label(parameter, unit),
            "time_unit": time_unit,
            "series": items,
        }

    def overlays(self, parameter, flags, window_size=""):
        """
        Return enabled derived overlays using the shared feature evaluators.
        """
        options = PlotOptions(
            mean=bool(flags.get("mean")),
            median=bool(flags.get("median")),
            cummulative_average=bool(flags.get("cummulative_average")),
            self_correlation_mean=bool(flags.get("self_correlation_mean")),
            difference=bool(flags.get("difference")),
            running_average=bool(flags.get("running_average")),
            window_size=str(window_size or ""),
        )
        with self.lock:
            energies = list(self.reader.energies)
            computed = list(iter_time_series_overlays(
                energies, parameter, options, window_policy="clamp"))
        guides = []
        for overlay in computed:
            time, values, _ = _downsample(
                np.asarray(overlay.time, dtype=float),
                np.asarray(overlay.values, dtype=float),
                MAX_POINTS,
            )
            guides.append({
                "key": overlay.feature.key,
                "label": overlay.label,
                "time": _json_list(time),
                "values": _json_list(values),
            })
        return {"parameter": parameter, "overlays": guides}

    def histogram(self, parameter, bins=HISTOGRAM_BINS_DEFAULT):
        """
        Return per-file counts on shared edges plus mean/median guides.
        """
        bins = max(8, min(200, int(bins)))
        with self.lock:
            energies = list(self.reader.energies)
        matching = _matching_indices(energies, parameter)
        if not matching:
            raise ValueError(
                f"Parameter {parameter} is not present in any input file.")
        unit = parameter_unit_for_energies(energies, parameter)
        combined = concatenate_series(energies, parameter)
        finite = np.asarray(combined.values, dtype=float)
        finite = finite[np.isfinite(finite)]
        if finite.size == 0:
            raise ValueError(
                f"Parameter {parameter} has no finite values to bin.")
        if finite.min() == finite.max():
            edges = np.linspace(
                finite.min() - 0.5, finite.max() + 0.5, bins + 1)
        else:
            edges = np.histogram_bin_edges(finite, bins=bins)
        options = PlotOptions(mean=True, median=True)
        guides = [
            {"label": guide.label, "value": float(guide.value)}
            for guide in iter_histogram_guides(energies, parameter, options)
        ]
        items = []
        kde = []
        for index in matching:
            values = np.asarray(
                series(energies[index], parameter).values, dtype=float)
            values = values[np.isfinite(values)]
            counts, _ = np.histogram(values, bins=edges)
            items.append({
                "label": self.labels[index],
                "rows": int(values.size),
                "counts": [int(count) for count in counts],
            })
            curve = _kde_of(values, edges)
            if curve is not None:
                curve["label"] = self.labels[index]
                kde.append(curve)
        return {
            "parameter": parameter,
            "unit": unit,
            "label": parameter_label(parameter, unit),
            "edges": [float(edge) for edge in edges],
            "series": items,
            "guides": guides,
            "kde": kde,
        }

    def summaries(self):
        """
        Return compact stats plus sparkline values for every parameter.

        Parameters are independent (numpy releases the GIL), so they are
        evaluated in a small thread pool instead of one by one. The whole
        payload is cached per file snapshot: file contents cannot change
        without a refresh, which clears the cache.
        """
        with self.lock:
            energies = list(self.reader.energies)
            cache_key = _snapshot_key(self.snapshot)
            cached = self._summaries_cache.get(cache_key)
        if cached is not None:
            return cached
        names = available_parameters(energies, include_time=False)
        payload = {"summaries": [
            self._summary_entry(energies, name) for name in names
        ]}
        with self.lock:
            if _snapshot_key(self.snapshot) == cache_key:
                self._summaries_cache[cache_key] = payload
        return payload

    def _compute_summaries(self, energies):
        """
        Evaluate the dashboard payload for one energy snapshot.
        """
        names = available_parameters(energies, include_time=False)
        items = list(self.pool.map(
            lambda name: self._summary_entry(energies, name), names))
        return {"summaries": items}

    def _summary_entry(self, energies, name):
        """
        Return the dashboard payload for one parameter.
        """
        matching = _matching_indices(energies, name)
        try:
            unit = parameter_unit_for_energies(energies, name)
        except ValueError:
            unit = ""
        stats = [
            _stats_for(energies[index], name, self.labels[index])
            for index in matching
        ]
        try:
            combined = concatenate_series(energies, name)
            values = np.asarray(combined.values, dtype=float)
            time = np.asarray(combined.time, dtype=float)
            finite = values[np.isfinite(values)]
            _, spark, _ = _downsample(time, values, SPARK_POINTS)
            spark = [v for v in _json_list(spark) if v is not None]
            combined_stats = _stats_of_array(
                finite, label="combined", rows=int(values.size))
            kind = parameter_kind(name, finite)
            if kind == "observable":
                combined_stats["analysis"] = _analysis_of(values, time)
            hist = _mini_histogram(finite)
        except ValueError:
            combined_stats = None
            kind = parameter_kind(name)
            spark = []
            hist = None
        return {
            "name": name,
            "unit": unit,
            "label": parameter_label(name, unit),
            "files": stats,
            "combined": combined_stats,
            "spark": spark,
            "hist": hist,
            "kind": kind,
        }

    def summary(self, parameter):
        """
        Return per-file and combined stats for one parameter.
        """
        with self.lock:
            energies = list(self.reader.energies)
        matching = _matching_indices(energies, parameter)
        if not matching:
            raise ValueError(
                f"Parameter {parameter} is not present in any input file.")
        unit = parameter_unit_for_energies(energies, parameter)
        files = [
            _stats_for(energies[index], parameter, self.labels[index])
            for index in matching
        ]
        combined_series = concatenate_series(energies, parameter)
        values = np.asarray(combined_series.values, dtype=float)
        time = np.asarray(combined_series.time, dtype=float)
        combined = _stats_of_array(
            values[np.isfinite(values)],
            label="combined",
            rows=int(values.size),
        )
        kind = parameter_kind(parameter, values)
        if kind == "observable":
            combined["analysis"] = _analysis_of(values, time)
        return {
            "parameter": parameter,
            "unit": unit,
            "label": parameter_label(parameter, unit),
            "files": files,
            "combined": combined,
            "kind": kind,
        }

    def export_csv(self, parameter):
        """
        Return long-form CSV (file,time,value) with a commented header.
        """
        with self.lock:
            energies = list(self.reader.energies)
        matching = _matching_indices(energies, parameter)
        if not matching:
            raise ValueError(
                f"Parameter {parameter} is not present in any input file.")
        unit = parameter_unit_for_energies(energies, parameter)
        time_label = axis_label(energies[0]) if energies else "time"
        lines = [
            f"# parameter: {parameter}",
            f"# unit: {unit or 'n/a'}",
            f"# time: {time_label}",
            "file,time,value",
        ]
        for index in matching:
            energy = energies[index]
            time = np.asarray(simulation_time(energy), dtype=float)
            values = np.asarray(
                series(energy, parameter).values, dtype=float)
            label = self.labels[index]
            for stamp, value in zip(time, values):
                if math.isfinite(stamp) and math.isfinite(value):
                    lines.append(f"{label},{stamp:.10g},{value:.10g}")
        return "\n".join(lines) + "\n"


def _time_unit(energies):
    """
    Return the simulation-time unit, or an empty string when unknown.
    """
    for energy in energies:
        unit = getattr(energy, "simulation_time_unit", None)
        if unit:
            return unit
        unit = getattr(energy, "units", {}).get("SIMULATION-TIME")
        if unit:
            return unit
    return ""


def _analysis_of(values, time):
    """
    Return equilibration and correlation diagnostics for combined values.

    ``sem``/``inefficiency``/``correlation_time``/``n_effective`` come from
    Flyvbjerg-Petersen blocking; ``equil_index``/``equil_time`` from the
    batched MSER truncation rule. Everything is ``None`` when the series is
    too short or has no spread.
    """
    finite_time = np.asarray(time, dtype=float)
    finite = np.asarray(values, dtype=float)
    mask = np.isfinite(finite) & np.isfinite(finite_time)
    finite, finite_time = finite[mask], finite_time[mask]
    sem, inefficiency, tau, n_effective = Statistic.block_error_values(
        finite_time, finite)
    equil_index = Statistic.mser_truncation_index(finite)
    if equil_index is None:
        return {
            "sem": sem,
            "inefficiency": inefficiency,
            "correlation_time": tau,
            "n_effective": n_effective,
            "equil_index": None,
            "equil_time": None,
            "discarded_fraction": None,
            "equilibrated": None,
        }
    equil_time = float(finite_time[min(equil_index, finite_time.size - 1)])
    fraction = equil_index / max(finite.size, 1)
    return {
        "sem": sem,
        "inefficiency": inefficiency,
        "correlation_time": tau,
        "n_effective": n_effective,
        "equil_index": int(equil_index),
        "equil_time": equil_time,
        "discarded_fraction": float(fraction),
        "equilibrated": bool(fraction <= 0.5),
    }


def _kde_of(finite, edges):
    """
    Return a Gaussian KDE sampled on a grid, scaled to histogram counts.

    Returns ``None`` when scipy is unavailable or the data has no spread.
    """
    try:
        from scipy.stats import gaussian_kde
    except ImportError:
        return None
    values = np.asarray(finite, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 8 or float(np.std(values)) == 0:
        return None
    stride = max(1, values.size // 20000)
    sample = values[::stride]
    try:
        density = gaussian_kde(sample)
    except (ValueError, np.linalg.LinAlgError):
        return None
    grid = np.linspace(float(edges[0]), float(edges[-1]), 200)
    try:
        evaluated = np.asarray(density(grid), dtype=float)
    except (ValueError, np.linalg.LinAlgError):
        return None
    if not np.all(np.isfinite(evaluated)):
        return None
    bin_width = float(np.mean(np.diff(edges)))
    scaled = evaluated * values.size * bin_width
    return {
        "x": [float(value) for value in grid],
        "y": [float(value) for value in scaled],
    }


def _mini_histogram(finite, bins=24):
    """
    Return compact shared-edge counts for dashboard mini histograms.
    """
    values = np.asarray(finite, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return None
    if values.min() == values.max():
        edges = np.linspace(
            values.min() - 0.5, values.max() + 0.5, bins + 1)
    else:
        edges = np.histogram_bin_edges(values, bins=bins)
    counts, _ = np.histogram(values, bins=edges)
    return {
        "edges": [float(edge) for edge in edges],
        "counts": [int(count) for count in counts],
    }


def _snapshot_key(snapshot):
    """
    Return a hashable key for a file snapshot mapping.
    """
    return tuple(sorted(
        (filename, state) for filename, state in snapshot.items()))


def _snapshot_files(filenames):
    """
    Return mtime+size per file (None when a file is temporarily missing).
    """
    snapshot = {}
    for filename in filenames:
        try:
            stat = os.stat(filename)
            snapshot[filename] = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            snapshot[filename] = None
    return snapshot


def _row_count(energy):
    """
    Return the row count backing one energy-like object.
    """
    try:
        return int(np.asarray(simulation_time(energy)).size)
    except (ValueError, TypeError, AttributeError):
        return 0


def _matching_indices(energies, parameter):
    """
    Return indices of files exposing a parameter, in reader order.
    """
    return [
        index for index, energy in enumerate(energies)
        if parameter in getattr(energy, "info", {})
    ]


def _kind_of(energies, parameter):
    """
    Classify a parameter from its combined values (name-only fallback
    when the series cannot be concatenated).
    """
    try:
        combined = concatenate_series(energies, parameter)
        values = np.asarray(combined.values, dtype=float)
    except ValueError:
        values = None
    return parameter_kind(parameter, values)


def _downsample(time, values, max_points):
    """
    Stride downsample paired arrays, returning arrays plus stride used.
    """
    count = int(min(time.size, values.size))
    time, values = time[:count], values[:count]
    if count <= max_points or count == 0:
        return time, values, 1
    stride = math.ceil(count / max_points)
    return time[::stride], values[::stride], stride


def _json_list(array):
    """
    Convert a float array to a JSON-safe list (non-finite becomes null).
    """
    return [
        None if not math.isfinite(value) else float(value)
        for value in np.asarray(array, dtype=float).tolist()
    ]


def _finite_min(values):
    """
    Return the finite minimum or None for empty/all-NaN input.
    """
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return float(finite.min()) if finite.size else None


def _finite_max(values):
    """
    Return the finite maximum or None for empty/all-NaN input.
    """
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return float(finite.max()) if finite.size else None


def _stats_for(energy, parameter, label):
    """
    Return display stats for one file's parameter series.
    """
    values = np.asarray(series(energy, parameter).values, dtype=float)
    return _stats_of_array(
        values[np.isfinite(values)], label=label, rows=int(values.size))


def _stats_of_array(finite, label, rows):
    """
    Return display stats for finite values with a total row count.

    ``drift`` is the second-half mean minus the first-half mean in units
    of overall standard deviation: the dashboard's steady/drifting signal.
    """
    if finite.size == 0:
        return {
            "label": label, "rows": rows, "latest": None, "mean": None,
            "median": None, "std": None, "min": None, "max": None,
            "drift": None,
        }
    return {
        "label": label,
        "rows": rows,
        "latest": float(finite[-1]),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "std": float(np.std(finite)),
        "min": float(finite.min()),
        "max": float(finite.max()),
        "drift": _drift_sigma(finite),
    }


def _drift_sigma(finite):
    """
    Return half-vs-half mean shift in standard deviations, else None.
    """
    if finite.size < 4:
        return None
    std = float(np.std(finite))
    if std == 0 or not math.isfinite(std):
        return None
    half = finite.size // 2
    drift = (
        float(np.mean(finite[half:])) - float(np.mean(finite[:half]))
    ) / std
    return drift if math.isfinite(drift) else None
