import pytest

from PQEnalyzer.classes import Reader
from PQEnalyzer.classes import App
from PQEnalyzer.classes import PlotTime
from PQEnalyzer.classes.plot import Plot

from PQAnalysis.traj.formats import MDEngineFormat

class TestPlot:
    """
    Test the Plot class.

    ...

    Attributes
    ----------
    example_dir : str
        The directory of the example files.

    Methods
    -------
    test__init__()
        Test the initialization of the Plot object.
    test_main_data()
        Test the main_data method of the Plot object.
    test_labels()
        Test the labels method of the Plot object.
    test_plot()
        Test the plot method of the Plot object.
    test_statistics()
        Test the statistics method of the Plot object.
    test_live_plot()
        Test the live_plot method of the Plot object.
    """
    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test__init__(self, example_dir):
        """
        Test the initialization of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert isinstance(plot, PlotTime)
        assert issubclass(PlotTime, Plot)
        assert plot.reader == reader
        assert plot.app == app
        assert plot.plot_frame is not None
        assert plot.ax is not None

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_main_data(self, example_dir):
        """
        Test the main_data method of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert getattr(plot, "main_data", None) is not None
        assert callable(getattr(plot, "main_data"))

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_labels(self, example_dir):
        """
        Test the labels method of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert getattr(plot, "labels", None) is not None
        assert callable(getattr(plot, "labels"))

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_plot(self, example_dir):
        """
        Test the plot method of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert getattr(plot, "plot", None) is not None
        assert callable(getattr(plot, "plot"))

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_statistics(self, example_dir):
        """
        Test the statistics method of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert getattr(plot, "statistics", None) is not None
        assert callable(getattr(plot, "statistics"))

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_live_plot(self, example_dir):
        """
        Test the live_plot method of the Plot object.
        """
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = PlotTime(app)
        assert getattr(plot, "live_plot", None) is not None
        assert callable(getattr(plot, "live_plot"))
