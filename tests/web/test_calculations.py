"""Scientific edge cases for the combined-data web calculations."""

import json

import numpy as np

from PQEnalyzer.web.calculations import (
    _analysis_of,
    _automatic_bin_count,
    _drift_sigma,
    _json_list,
    _kde_of,
    _mini_histogram,
    _stats_of_array,
)


def test_short_or_constant_sequences_have_no_convergence_measure():
    short = np.asarray([3.0, 4.0])
    assert _drift_sigma(short) is None
    assert _analysis_of(short, np.arange(short.size))["equil_index"] is None
    constant = np.full(20, 7.0)
    assert _automatic_bin_count(constant) == 1
    assert _stats_of_array(constant, "combined", 20)["drift"] is None


def test_missing_values_stay_missing_in_transport_and_empty_stats():
    assert _json_list([1, np.nan, np.inf, -np.inf]) == [1.0, None, None, None]
    assert _mini_histogram(np.asarray([np.nan])) is None
    empty = _stats_of_array(np.asarray([]), "combined", 3)
    assert empty["rows"] == 3
    assert empty["mean"] is None
    assert empty["drift"] is None


def test_overflowed_estimates_are_unavailable_and_json_safe():
    values = np.asarray([-1e200, 1e200, -1e200, 1e200])
    time = np.arange(values.size)

    stats = _stats_of_array(values, "combined", values.size)
    analysis = _analysis_of(values, time)

    assert stats["mean"] == 0.0
    assert stats["std"] is None
    assert analysis["sem"] is None
    assert analysis["equil_index"] is None
    json.dumps({"stats": stats, "analysis": analysis}, allow_nan=False)


def test_auto_bins_bound_a_long_tailed_distribution():
    values = np.r_[np.zeros(1000), np.arange(1, 1001, dtype=float)]
    assert 2 <= _automatic_bin_count(values) <= 200


def test_kde_drops_nonfinite_density(monkeypatch):
    from scipy import stats

    monkeypatch.setattr(
        stats, "gaussian_kde",
        lambda sample: lambda grid: np.full(grid.shape, np.nan),
    )
    values = np.linspace(0.0, 1.0, 20)
    assert _kde_of(values, np.linspace(0.0, 1.0, 5)) is None
