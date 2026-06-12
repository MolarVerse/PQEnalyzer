"""
Shared plot feature definitions and evaluators.
"""

from dataclasses import dataclass, field

from ..energy_access import (
    concatenate_series,
    difference_series,
)
from ..statistics import Statistic


@dataclass(frozen=True)
class PlotFeature:
    """
    One plot feature exposed by both GUI and TUI controls.
    """

    key: str
    label: str
    shortcut: str
    group: str
    view_attribute: str | None = None
    time_series: bool = True
    histogram: bool = False
    default: bool = False
    matplotlib_style: dict = field(default_factory=dict)

    @property
    def option_attribute(self):
        """
        Return the PlotOptions attribute used for this feature.
        """

        return self.key

    @property
    def gui_attribute(self):
        """
        Return the view attribute used for this feature widget.
        """

        return self.view_attribute or self.key

    @property
    def short_label(self):
        """
        Return a compact label for terminal controls.
        """

        if self.key == "cummulative_average":
            return "cumulative"
        if self.key == "self_correlation_mean":
            return "self-corr"
        if self.key == "difference":
            return "difference"
        if self.key == "running_average":
            return "running avg"
        return self.label.lower()


@dataclass(frozen=True)
class PlotSeries:
    """
    A computed time-series overlay.
    """

    feature: PlotFeature
    label: str
    time: object
    values: object


@dataclass(frozen=True)
class HistogramGuide:
    """
    A computed vertical guide for histogram plots.
    """

    feature: PlotFeature
    label: str
    value: float


STATISTIC_FEATURES = (
    PlotFeature(
        key="mean",
        label="Mean",
        shortcut="m",
        group="statistics",
        histogram=True,
        matplotlib_style={
            "linestyle": "--",
            "linewidth": 1.15,
            "alpha": 0.85,
            "zorder": 3,
        },
    ),
    PlotFeature(
        key="median",
        label="Median",
        shortcut="n",
        group="statistics",
        histogram=True,
        matplotlib_style={
            "linestyle": ":",
            "linewidth": 1.35,
            "alpha": 0.9,
            "zorder": 3,
        },
    ),
)

TIME_SERIES_FEATURES = (
    PlotFeature(
        key="cummulative_average",
        label="Cumulative Average",
        shortcut="c",
        group="time_series",
        view_attribute="cumulative_average",
        matplotlib_style={
            "linestyle": "-.",
            "linewidth": 1.45,
            "alpha": 0.9,
            "zorder": 3,
        },
    ),
    PlotFeature(
        key="self_correlation_mean",
        label="Self-Correlation Mean",
        shortcut="s",
        group="time_series",
        matplotlib_style={
            "linestyle": (0, (2, 2)),
            "linewidth": 1.45,
            "alpha": 0.9,
            "zorder": 3,
        },
    ),
    PlotFeature(
        key="difference",
        label="Difference (1 - 2)",
        shortcut="x",
        group="time_series",
        matplotlib_style={
            "linestyle": "-",
            "linewidth": 1.9,
            "alpha": 0.95,
            "zorder": 4,
        },
    ),
    PlotFeature(
        key="running_average",
        label="Running Average",
        shortcut="a",
        group="time_series",
        matplotlib_style={
            "linestyle": "-",
            "linewidth": 2.0,
            "alpha": 0.95,
            "zorder": 4,
        },
    ),
)

PLOT_FEATURES = STATISTIC_FEATURES + TIME_SERIES_FEATURES
PLOT_FEATURES_BY_KEY = {
    feature.key: feature
    for feature in PLOT_FEATURES
}


def enabled_features(options):
    """
    Yield enabled plot features from a PlotOptions-like object.
    """

    for feature in PLOT_FEATURES:
        if getattr(options, feature.option_attribute):
            yield feature


def enabled_feature_labels(options):
    """
    Return compact labels for enabled features.
    """

    if options.difference:
        return [PLOT_FEATURES_BY_KEY["difference"].short_label]

    labels = [
        feature.short_label
        for feature in enabled_features(options)
    ]
    return labels or ["none"]


def iter_time_series_overlays(
    energies,
    info_parameter,
    options,
    *,
    window_policy="strict",
):
    """
    Yield enabled time-series overlays for a parameter.
    """

    if options.difference:
        feature = PLOT_FEATURES_BY_KEY["difference"]
        delta_series = difference_series(energies, info_parameter)
        yield PlotSeries(
            feature=feature,
            label=feature.label,
            time=delta_series.time,
            values=delta_series.values,
        )
        return

    energy_series = concatenate_series(energies, info_parameter)

    if options.mean:
        feature = PLOT_FEATURES_BY_KEY["mean"]
        time, values = Statistic.mean_values(
            energy_series.time,
            energy_series.values,
        )
        yield PlotSeries(feature, feature.label, time, values)

    if options.median:
        feature = PLOT_FEATURES_BY_KEY["median"]
        time, values = Statistic.median_values(
            energy_series.time,
            energy_series.values,
        )
        yield PlotSeries(feature, feature.label, time, values)

    if options.cummulative_average:
        feature = PLOT_FEATURES_BY_KEY["cummulative_average"]
        time, values = Statistic.cumulative_average_values(
            energy_series.time,
            energy_series.values,
        )
        yield PlotSeries(feature, feature.label, time, values)

    if options.self_correlation_mean:
        feature = PLOT_FEATURES_BY_KEY["self_correlation_mean"]
        time, values = Statistic.self_correlation_mean_values(
            energy_series.time,
            energy_series.values,
        )
        yield PlotSeries(feature, feature.label, time, values)

    if options.running_average:
        feature = PLOT_FEATURES_BY_KEY["running_average"]
        window_size = running_average_window(
            energy_series.values,
            options.window_size,
            policy=window_policy,
        )
        time, values = Statistic.running_average_values(
            energy_series.time,
            energy_series.values,
            window_size,
        )
        yield PlotSeries(
            feature,
            f"{feature.label} ({window_size})",
            time,
            values,
        )


def iter_histogram_guides(energies, info_parameter, options):
    """
    Yield enabled histogram guide values for a parameter.
    """

    energy_series = concatenate_series(energies, info_parameter)

    if options.mean:
        feature = PLOT_FEATURES_BY_KEY["mean"]
        _, values = Statistic.mean_values(
            energy_series.time,
            energy_series.values,
        )
        yield HistogramGuide(feature, feature.label, float(values[0]))

    if options.median:
        feature = PLOT_FEATURES_BY_KEY["median"]
        _, values = Statistic.median_values(
            energy_series.time,
            energy_series.values,
        )
        yield HistogramGuide(feature, feature.label, float(values[0]))


def running_average_window(values, requested_window_size, *, policy):
    """
    Return a positive running-average window for a series.
    """

    try:
        window_size = _parse_window_size(requested_window_size)
    except ValueError:
        if policy != "clamp":
            raise
        window_size = len(values)

    if policy == "clamp":
        window_size = min(window_size, len(values))

    return window_size


def _parse_window_size(requested_window_size):
    """
    Parse a positive running-average window size.
    """

    requested = str(requested_window_size).strip()
    if requested in {"", "."}:
        return 1000

    window_size = int(float(requested))
    if window_size < 1:
        raise ValueError("Window size must be positive")

    return window_size
