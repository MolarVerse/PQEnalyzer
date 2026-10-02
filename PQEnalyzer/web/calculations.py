"""Pure chart calculations and JSON-safe numeric shaping for the web API."""

import math

import numpy as np

from ..statistics import Statistic


def _chart_axis(time, label, unit):
    """Keep ordered physical time; use sample position after a restart.

    A charting library cannot put two different observations at the same x
    value. A sample axis retains every point when input files overlap or
    reset their simulation-time counter.
    """
    ordered = np.asarray(time, dtype=float)
    if np.all(np.isfinite(ordered)) and np.all(np.diff(ordered) > 0):
        return ordered, label, unit
    return np.arange(1, ordered.size + 1, dtype=float), "Sample", ""


def _analysis_of(values, time):
    """
    Return truncation and correlation estimates for combined values.

    ``sem``/``inefficiency``/``correlation_time``/``n_effective`` come from
    FFT autocorrelation with Geyer's initial-positive-sequence truncation;
    ``equil_index``/``equil_time`` come from the batched MSER rule. MSER
    estimates an initial cut and does not establish that sampling is sufficient.
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
    }


def _automatic_bin_count(values):
    """Use NumPy's auto estimators while bounding the resulting chart size."""
    count = values.size
    span = float(np.ptp(values))
    if count < 2 or span == 0:
        return 1
    sturges = math.log2(count) + 1
    lower, upper = np.percentile(values, [25, 75])
    iqr = float(upper - lower)
    fd_width = 2 * iqr / count ** (1 / 3) if iqr > 0 else 0
    fd_bins = span / fd_width if fd_width > 0 else 0
    if not math.isfinite(fd_bins):
        return 200
    return max(2, min(200, math.ceil(max(sturges, fd_bins))))


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


def _downsample(time, values, max_points):
    """
    Preserve endpoints, local extrema, and a missing-value gap per bucket.

    Uniform striding can erase a short physical spike entirely. Each bucket
    contributes at most three points, keeping the response within the budget.
    """
    count = int(min(time.size, values.size))
    time, values = time[:count], values[:count]
    max_points = max(2, int(max_points))
    if count <= max_points or count == 0:
        return time, values
    if max_points < 5:
        indices = np.linspace(0, count - 1, max_points, dtype=int)
        return time[indices], values[indices]

    bucket_count = min(count - 2, (max_points - 2) // 3)
    edges = np.linspace(1, count - 1, bucket_count + 1, dtype=int)
    indices = [0]
    for start, stop in zip(edges[:-1], edges[1:]):
        bucket = values[start:stop]
        finite = np.flatnonzero(np.isfinite(bucket))
        if finite.size:
            indices.extend((
                start + int(finite[np.argmin(bucket[finite])]),
                start + int(finite[np.argmax(bucket[finite])]),
            ))
        missing = np.flatnonzero(~np.isfinite(bucket))
        if missing.size:
            indices.append(start + int(missing[0]))
    indices.append(count - 1)
    selected = np.unique(indices)
    return time[selected], values[selected]


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


def _finite_float_or_none(value):
    """Return a finite JSON number, or ``None`` for an overflowed result."""
    number = float(value)
    return number if math.isfinite(number) else None


def _stats_of_array(finite, label, rows):
    """
    Return display stats for finite values with a total row count.

    ``drift`` is the second-half mean minus the first-half mean in units
    of overall standard deviation. It is descriptive, not a convergence test.
    """
    if finite.size == 0:
        return {
            "label": label, "rows": rows, "latest": None, "mean": None,
            "median": None, "std": None, "min": None, "max": None,
            "drift": None,
        }
    with np.errstate(over="ignore", invalid="ignore"):
        mean = np.mean(finite)
        median = np.median(finite)
        std = np.std(finite)
    return {
        "label": label,
        "rows": rows,
        "latest": float(finite[-1]),
        "mean": _finite_float_or_none(mean),
        "median": _finite_float_or_none(median),
        "std": _finite_float_or_none(std),
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
    with np.errstate(over="ignore", invalid="ignore"):
        std = float(np.std(finite))
    if std == 0 or not math.isfinite(std):
        return None
    half = finite.size // 2
    with np.errstate(over="ignore", invalid="ignore"):
        drift = (
            float(np.mean(finite[half:])) - float(np.mean(finite[:half]))
        ) / std
    return drift if math.isfinite(drift) else None
