"""
Test the performance of the Statistic class
"""
import pytest

from PQAnalysis.traj import MDEngineFormat
from PQEnalyzer.readers import Reader
from PQEnalyzer.statistics import Statistic


@pytest.mark.benchmark(group="Statistic")
def test_statistic_benchmark(benchmark):
    """
    Tests the performance of the Statistic class.
    """

    energies = Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies

    def setup():
        return Statistic.running_average(energies, "SIMULATION-TIME", 2)

    benchmark.pedantic(setup, iterations=10, rounds=100)
