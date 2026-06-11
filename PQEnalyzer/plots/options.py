"""
Plot option state shared by GUI plot windows.
"""

from dataclasses import dataclass


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

    @classmethod
    def from_app(cls, app):
        """
        Read the current option widgets from the GUI app.
        """

        return cls(
            mean=bool(app.mean.get()),
            median=bool(app.median.get()),
            cummulative_average=bool(app.cummulative_average.get()),
            self_correlation_mean=bool(app.self_correlation_mean.get()),
            difference=bool(app.difference.get()),
            running_average=bool(app.running_average.get()),
            window_size=app.window_size.get(),
            plot_main=bool(app.plot_main_data.get()),
        )
