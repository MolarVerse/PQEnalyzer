"""
Reader adapter for PQAnalysis box files.

PQAnalysis owns the box-file parsing. This adapter presents parsed box data
with the same small attribute surface that PQEnalyzer's existing plot code
uses for energy data: ``info``, ``units``, ``data`` and ``simulation_time``.
"""

from dataclasses import dataclass

import numpy as np
from PQAnalysis.core.cell import Cell
from PQAnalysis.io import read_box


BOX_PARAMETER_UNITS = (
    ("SIMULATION-TIME", "step"),
    ("BOX-X", "A"),
    ("BOX-Y", "A"),
    ("BOX-Z", "A"),
    ("ALPHA", "deg"),
    ("BETA", "deg"),
    ("GAMMA", "deg"),
    ("BOX-VOLUME", "A^3"),
)


@dataclass(frozen=True)
class BoxData:
    """
    PQAnalysis box arrays exposed through the plotting data interface.
    """

    steps: np.ndarray
    box_lengths: np.ndarray
    box_angles: np.ndarray
    info: dict
    units: dict
    data: dict
    simulation_time: np.ndarray

    @classmethod
    def from_pqanalysis(cls, steps, box_lengths, box_angles):
        """
        Build a plot-compatible box data object from PQAnalysis arrays.
        """

        steps = np.asarray(steps)
        box_lengths = np.asarray(box_lengths)
        box_angles = np.asarray(box_angles)

        data = {
            "SIMULATION-TIME": steps,
            "BOX-X": box_lengths[:, 0],
            "BOX-Y": box_lengths[:, 1],
            "BOX-Z": box_lengths[:, 2],
            "ALPHA": box_angles[:, 0],
            "BETA": box_angles[:, 1],
            "GAMMA": box_angles[:, 2],
            "BOX-VOLUME": np.asarray([
                Cell(x, y, z, alpha, beta, gamma).volume
                for (x, y, z), (alpha, beta, gamma)
                in zip(box_lengths, box_angles)
            ]),
        }

        return cls(
            steps=steps,
            box_lengths=box_lengths,
            box_angles=box_angles,
            info={parameter: parameter
                  for parameter, _ in BOX_PARAMETER_UNITS},
            units=dict(BOX_PARAMETER_UNITS),
            data=data,
            simulation_time=steps,
        )


class BoxReader:
    """
    Read PQAnalysis box files and expose them to existing plot code.
    """

    def __init__(self, filenames):
        """
        Read the configured box files immediately.
        """

        self.energies = []
        self.filenames = list(filenames)
        self.read()

    def read(self):
        """
        Read all box files through PQAnalysis.
        """

        self.__validate_filenames()
        self.energies = [
            self.__read_box_file(filename) for filename in self.filenames
        ]

    def read_last(self):
        """
        Refresh only the last configured box file.
        """

        self.__validate_filenames()
        self.energies[-1] = self.__read_box_file(self.filenames[-1])

    def __read_box_file(self, filename):
        """
        Read one box file through PQAnalysis and adapt it for plotting.
        """

        steps, box_lengths, box_angles = read_box(filename)
        return BoxData.from_pqanalysis(steps, box_lengths, box_angles)

    def __validate_filenames(self):
        """
        Reject empty input before handing control to PQAnalysis.
        """

        if len(self.filenames) == 0:
            raise ValueError(
                "The list of filenames is empty. Provide a list of filenames.")
