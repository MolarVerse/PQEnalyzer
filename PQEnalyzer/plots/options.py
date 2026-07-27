"""
Plot option state shared by GUI plot windows.
"""

from dataclasses import asdict, dataclass, fields

from .features import PLOT_FEATURES, PLOT_FEATURES_BY_KEY


@dataclass
class PlotOptions:
    """
    Snapshot of GUI-controlled plot options for one plot window.
    """

    mean: bool = False
    median: bool = False
    cummulative_average: bool = False
    self_correlation_mean: bool = False
    difference: bool = False
    running_average: bool = False
    window_size: str = ""
    plot_main: bool = False

    def __getattr__(self, name):
        """
        Return registry defaults for feature attributes added at runtime.
        """

        feature = PLOT_FEATURES_BY_KEY.get(name)
        if feature is not None:
            return feature.default

        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}")

    @classmethod
    def from_app(cls, app):
        """
        Read the current option widgets from the GUI app.
        """

        options = cls(
            window_size=app.window_size.get(),
            plot_main=bool(app.plot_main_data.get()),
        )
        for feature in PLOT_FEATURES:
            setattr(
                options,
                feature.option_attribute,
                bool(getattr(app, feature.option_attribute).get()),
            )

        return options

    @classmethod
    def from_mapping(cls, values):
        """
        Restore known options from persistent settings.
        """

        if not isinstance(values, dict):
            return cls()

        options = cls()
        for option_field in fields(cls):
            value = values.get(
                option_field.name,
                getattr(options, option_field.name),
            )
            default = getattr(options, option_field.name)
            if isinstance(default, bool):
                if isinstance(value, bool):
                    setattr(options, option_field.name, value)
            elif isinstance(value, str):
                setattr(options, option_field.name, value)

        return options

    def to_mapping(self):
        """
        Return JSON-compatible option values.
        """

        return asdict(self)

    @classmethod
    def with_enabled(cls, *feature_keys):
        """
        Return options with selected feature keys enabled.
        """

        options = cls()
        for feature_key in feature_keys:
            setattr(options, feature_key, True)
        return options
