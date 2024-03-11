import pytest
import os
from PQEnalyzer.classes.reader import Reader
from PQEnalyzer.classes.app import App
from PQEnalyzer.classes.plot import Plot
from PQAnalysis.traj.formats import MDEngineFormat
from PQAnalysis.physicalData.exceptions import EnergyError

class TestPlot:
    """
    Test the Plot class.
    """
    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test__init__(self, example_dir):
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]
        reader = Reader(list_filenames, MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        plot = Plot(app)
        assert plot.reader == reader
        assert plot.app == app