"""
Reader adapter for PQ optimizer output files.

PQAnalysis owns parsing, schema validation, and storage. This adapter keeps the
multi-file and live-refresh interface shared by PQEnalyzer's GUI and TUI.
"""

from PQAnalysis.io import read_optimizer_file


class OptimizerReader:
    """
    Read PQ ``.opt`` files through PQAnalysis for GUI and TUI plotting.
    """

    def __init__(self, filenames):
        """
        Read the configured optimizer files immediately.
        """

        self.energies = []
        self.filenames = list(filenames)
        self.read()

    def read(self):
        """
        Read every configured optimizer file.
        """

        self._validate_filenames()
        energies = [
            self._read_optimizer_file(filename) for filename in self.filenames
        ]
        self.energies = energies

    def read_last(self):
        """
        Refresh only the last optimizer file for live monitoring.
        """

        self._validate_filenames()
        refreshed_energy = self._read_optimizer_file(self.filenames[-1])
        self.energies[-1] = refreshed_energy

    @staticmethod
    def _read_optimizer_file(filename):
        """
        Read one optimizer file and attach its UI axis label.
        """

        energy = read_optimizer_file(str(filename))
        energy.axis_label = "Optimization Step"
        return energy

    def _validate_filenames(self):
        """
        Reject empty input before handing control to PQAnalysis.
        """

        if not self.filenames:
            raise ValueError(
                "The list of filenames is empty. Provide a list of filenames.")
