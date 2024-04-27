import pytest
import os
import numpy as np

from PQEnalyzer.classes import Statistic, Reader

from PQAnalysis.traj import MDEngineFormat

class TestStatistic:
    
    def test__new__(self):
        with pytest.raises(TypeError):
            Statistic()

    def test_mean(self):
        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PIMD_QMCF).energies
        time, mean = Statistic.mean(energies, "SIMULATION-TIME")
        assert np.all(time == [1, 5])
        assert np.all(mean == [3, 3])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PIMD_QMCF).energies
        time, mean = Statistic.mean(energies2, "SIMULATION-TIME")
        assert np.all(time == [6, 10])
        assert np.all(mean == [8, 8])
         
