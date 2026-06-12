import numpy as np

from PQEnalyzer.plots.features import (
    PLOT_FEATURES,
    PLOT_FEATURES_BY_KEY,
    PlotFeature,
    enabled_feature_labels,
    iter_histogram_guides,
    iter_time_series_overlays,
)
from PQEnalyzer.plots.options import PlotOptions


class FakeEnergy:

    def __init__(self, values, time=None):
        if time is None:
            time = np.arange(1, len(values) + 1)
        self.info = {"PARAMETER": "PARAMETER"}
        self.units = {"PARAMETER": "unit"}
        self.data = {"PARAMETER": np.array(values, dtype=float)}
        self.simulation_time = np.array(time, dtype=float)


def test_registry_defines_shared_gui_and_tui_features():
    feature_keys = [feature.key for feature in PLOT_FEATURES]
    shortcuts = [feature.shortcut for feature in PLOT_FEATURES]

    assert feature_keys == [
        "mean",
        "median",
        "cummulative_average",
        "self_correlation_mean",
        "difference",
        "running_average",
    ]
    assert shortcuts == ["m", "n", "c", "s", "x", "a"]


def test_plot_options_can_read_registry_feature_defaults():
    PLOT_FEATURES_BY_KEY["temporary_feature"] = PlotFeature(
        key="temporary_feature",
        label="Temporary Feature",
        shortcut="t",
        group="statistics",
    )
    options = PlotOptions()

    try:
        assert options.temporary_feature is False
    finally:
        del PLOT_FEATURES_BY_KEY["temporary_feature"]


def test_time_series_overlay_evaluator_uses_enabled_features():
    options = PlotOptions.with_enabled(
        "mean",
        "median",
        "cummulative_average",
        "self_correlation_mean",
        "running_average",
    )
    options.window_size = "2"

    overlays = list(iter_time_series_overlays(
        [FakeEnergy([1, 2, 4, 8])],
        "PARAMETER",
        options,
    ))

    assert [overlay.label for overlay in overlays] == [
        "Mean",
        "Median",
        "Cumulative Average",
        "Self-Correlation Mean",
        "Running Average (2)",
    ]


def test_difference_feature_takes_precedence_over_other_overlays():
    options = PlotOptions.with_enabled("mean", "difference")

    overlays = list(iter_time_series_overlays(
        [
            FakeEnergy([5, 6, 7]),
            FakeEnergy([1, 2, 4]),
        ],
        "PARAMETER",
        options,
    ))

    assert [overlay.label for overlay in overlays] == ["Difference (1 - 2)"]
    assert np.all(overlays[0].values == [4, 4, 3])
    assert enabled_feature_labels(options) == ["difference"]


def test_histogram_guides_use_shared_feature_definitions():
    options = PlotOptions.with_enabled("mean", "median")

    guides = list(iter_histogram_guides(
        [FakeEnergy([1, 2, 3])],
        "PARAMETER",
        options,
    ))

    assert [guide.label for guide in guides] == ["Mean", "Median"]
    assert [guide.value for guide in guides] == [2.0, 2.0]
