import pytest
import numpy as np

from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.statistics import Statistic
from PQEnalyzer.readers import Reader


class TestStatistic:

    def test__new__(self):
        with pytest.raises(TypeError):
            Statistic()

    def test_mean(self):
        time, mean = Statistic.mean_values([1, 2, 3, 4, 5],
                                           [1, 2, 3, 4, 5])
        assert np.all(time == [1, 5])
        assert np.all(mean == [3, 3])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, mean = Statistic.mean(energies, "SIMULATION-TIME")
        assert np.all(time == [1, 5])
        assert np.all(mean == [3, 3])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, mean = Statistic.mean(energies2, "SIMULATION-TIME")
        assert np.all(time == [6, 10])
        assert np.all(mean == [8, 8])

    def test_median(self):
        time, median = Statistic.median_values([1, 2, 3, 4, 5],
                                               [1, 2, 3, 4, 5])
        assert np.all(time == [1, 5])
        assert np.all(median == [3, 3])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, median = Statistic.median(energies, "SIMULATION-TIME")
        assert np.all(time == [1, 5])
        assert np.all(median == [3, 3])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, median = Statistic.median(energies2, "SIMULATION-TIME")
        assert np.all(time == [6, 10])
        assert np.all(median == [8, 8])

    def test_cumulative_average(self):
        time, cumulative_average = Statistic.cumulative_average_values(
            [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(cumulative_average == [1, 1.5, 2, 2.5, 3])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, cumulative_average = Statistic.cumulative_average(
            energies, "SIMULATION-TIME")
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(cumulative_average == [1, 1.5, 2, 2.5, 3])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, cumulative_average = Statistic.cumulative_average(
            energies2, "SIMULATION-TIME")
        assert np.all(time == [6, 7, 8, 9, 10])
        assert np.all(cumulative_average == [6, 6.5, 7, 7.5, 8])

    def test_cummulative_average_keeps_backward_compatibility(self):
        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies

        old_time, old_average = Statistic.cummulative_average(
            energies, "SIMULATION-TIME")
        new_time, new_average = Statistic.cumulative_average(
            energies, "SIMULATION-TIME")

        assert np.all(old_time == new_time)
        assert np.all(old_average == new_average)

    def test_auto_correlation(self):
        time, auto_correlation = Statistic.auto_correlation_values(
            [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.allclose(auto_correlation, [1, 0.4, -0.1, -0.4, -0.4])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, auto_correlation = Statistic.auto_correlation(
            energies, "SIMULATION-TIME")
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.allclose(auto_correlation, [1, 0.4, -0.1, -0.4, -0.4])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, auto_correlation = Statistic.auto_correlation(
            energies2, "SIMULATION-TIME")
        assert np.all(time == [6, 7, 8, 9, 10])
        assert np.allclose(auto_correlation, [1, 0.4, -0.1, -0.4, -0.4])

    def test_auto_correlation_constant_data(self):
        time, auto_correlation = Statistic.auto_correlation_values(
            [1, 2, 3, 4, 5], [2, 2, 2, 2, 2])

        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(auto_correlation == [1, 0, 0, 0, 0])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies

        time, auto_correlation = Statistic.auto_correlation(
            energies, "E(INTRA)")

        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(auto_correlation == [1, 0, 0, 0, 0])

    def test_running_average(self):
        time, running_average = Statistic.running_average_values(
            [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], 2)
        assert np.all(time == [1.5, 2.5, 3.5, 4.5])
        assert np.all(running_average == [1.5, 2.5, 3.5, 4.5])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, running_average = Statistic.running_average(
            energies, "SIMULATION-TIME", 2)
        assert np.all(time == [1.5, 2.5, 3.5, 4.5])
        assert np.all(running_average == [1.5, 2.5, 3.5, 4.5])

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, running_average = Statistic.running_average(
            energies2, "SIMULATION-TIME", 2)
        assert np.all(time == [6.5, 7.5, 8.5, 9.5])
        assert np.all(running_average == [6.5, 7.5, 8.5, 9.5])

        time, running_average = Statistic.running_average(
            energies2, "SIMULATION-TIME", 1)
        assert np.all(time == [6, 7, 8, 9, 10])
        assert np.all(running_average == [6, 7, 8, 9, 10])

        with pytest.raises(ValueError):
            Statistic.running_average_values([1, 2], [1, 2], 3)

        with pytest.raises(ValueError):
            Statistic.running_average_values([1, 2], [1, 2], 0)

        with pytest.raises(ValueError):
            Statistic.running_average_values([1, 2], [1, 2], -1)

        with pytest.raises(ValueError):
            Statistic.running_average(energies2, "SIMULATION-TIME", 6)

        with pytest.raises(ValueError):
            Statistic.running_average(energies2, "SIMULATION-TIME", 0)

        with pytest.raises(ValueError):
            Statistic.running_average(energies2, "SIMULATION-TIME", -1)
