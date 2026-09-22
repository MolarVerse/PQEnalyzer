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

    def test_self_correlation_mean(self):
        time, self_correlation_mean = (
            Statistic.self_correlation_mean_values(
                [1, 2, 3, 4, 5], [1, 2, 3, 4, 5]))
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.allclose(
            self_correlation_mean,
            [2, 2.5, 3, 3.5, 4],
        )

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies
        time, self_correlation_mean = (
            Statistic.self_correlation_mean(energies, "SIMULATION-TIME"))
        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.allclose(
            self_correlation_mean,
            [2, 2.5, 3, 3.5, 4],
        )

        energies2 = Reader(["tests/data/md-02.en"], MDEngineFormat.PQ).energies
        time, self_correlation_mean = (
            Statistic.self_correlation_mean(energies2, "SIMULATION-TIME"))
        assert np.all(time == [6, 7, 8, 9, 10])
        assert np.allclose(
            self_correlation_mean,
            [7, 7.5, 8, 8.5, 9],
        )

    def test_self_correlation_mean_constant_data(self):
        time, self_correlation_mean = (
            Statistic.self_correlation_mean_values(
                [1, 2, 3, 4, 5], [2, 2, 2, 2, 2]))

        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(self_correlation_mean == [2, 2, 2, 2, 2])

        energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies

        time, self_correlation_mean = (
            Statistic.self_correlation_mean(energies, "E(INTRA)"))

        assert np.all(time == [1, 2, 3, 4, 5])
        assert np.all(self_correlation_mean == [0, 0, 0, 0, 0])

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

    def test_block_error_values(self):
        rng = np.random.default_rng(42)

        white = rng.normal(300.0, 15.0, size=20000)
        sem, inefficiency, tau, n_effective = Statistic.block_error_values(
            np.arange(20000), white)
        assert inefficiency == pytest.approx(1.0, abs=0.1)
        assert tau == pytest.approx(1.0, abs=0.1)
        assert n_effective == pytest.approx(20000, rel=0.05)
        assert sem == pytest.approx(15.0 / np.sqrt(20000), rel=0.05)

        correlated = np.zeros(20000)
        for index in range(1, 20000):
            correlated[index] = (
                0.95 * correlated[index - 1] + rng.normal(0.0, 4.68))
        _, inefficiency, tau, n_effective = Statistic.block_error_values(
            np.arange(20000), correlated)
        assert inefficiency == pytest.approx(39.0, rel=0.25)
        assert tau == pytest.approx(39.0, rel=0.25)
        assert n_effective == pytest.approx(20000 / 39.0, rel=0.25)

        assert Statistic.block_error_values(
            [1, 2, 3], [1.0, 2.0, 3.0]) == (None, None, None, None)

        sem, inefficiency, tau, n_effective = Statistic.block_error_values(
            [1, 2, 3, 4, 5], [2.0, 2.0, 2.0, 2.0, 2.0])
        assert (sem, inefficiency, tau, n_effective) == (0.0, 1.0, 1.0, 5.0)

    def test_mser_truncation_index(self):
        rng = np.random.default_rng(7)

        assert Statistic.mser_truncation_index(
            rng.normal(300.0, 15.0, size=20000)) <= 400

        drifted = np.concatenate([
            np.linspace(200.0, 400.0, 2000),
            rng.normal(300.0, 15.0, size=18000),
        ])
        assert Statistic.mser_truncation_index(drifted) == 2000

        assert Statistic.mser_truncation_index(np.full(100, 5.0)) == 0
        assert Statistic.mser_truncation_index([1.0, 2.0, 3.0]) is None
