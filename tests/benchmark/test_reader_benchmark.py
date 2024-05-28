"""
Benchmark the Reader class.
"""
import pytest

from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.readers import Reader


@pytest.mark.benchmark(group="Reader")
def test_reader_benchmark(benchmark):
    """
    Benchmark the Reader class.
    """

    def setup():
        return Reader(["tests/data/md-01.en"], MDEngineFormat.PQ).energies

    benchmark.pedantic(setup, iterations=10, rounds=100)
