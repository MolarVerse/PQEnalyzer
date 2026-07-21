"""
PQ energy-file compatibility helpers.

PQAnalysis owns energy parsing for normal PQ files. This module keeps one
PQEnalyzer compatibility path for PQ info files that contain a row with only
one parameter entry, which older PQAnalysis releases reject even though the
energy column is present.
"""

from pathlib import Path

import numpy as np
from PQAnalysis.io import EnergyFileReader
from PQAnalysis.physical_data import Energy


def read_single_column_pq_energy_file(filename):
    """
    Read a PQ energy file whose info file contains single-entry rows.

    Returns ``None`` when the matching info file does not need this
    compatibility path, allowing the caller to use the regular PQAnalysis
    reader. Numeric energy data and the final ``Energy`` object still come from
    PQAnalysis.
    """

    info_filename = Path(filename).with_suffix(".info")
    if not info_filename.exists():
        return None

    parsed_info = parse_single_column_pq_info_file(info_filename)
    if parsed_info is None:
        return None

    info, units = parsed_info
    energy = EnergyFileReader(
        str(filename),
        use_info_file=False,
    ).read()

    return Energy(_normalize_energy_data_for_info(energy.data, info), info,
                  units)


def _normalize_energy_data_for_info(data, info):
    """
    Return energy data with one row per parsed info parameter.
    """

    data = np.asarray(data)
    if data.ndim == 1:
        return data.reshape((len(data), 1))

    if len(data) == len(info):
        return data

    if data.shape[1] == len(info):
        return data.T

    return data


def parse_single_column_pq_info_file(filename):
    """
    Parse a PQ info file with at least one single-entry parameter row.

    Standard PQ rows contain two parameter entries and split into eight tokens.
    The compatibility row reported in issue #81 contains one parameter entry and
    splits into five tokens: ``| PARAMETER value unit |``.
    """

    info = {}
    units = {}
    entry_counter = 0
    has_single_column_row = False

    with open(filename, "r", encoding="utf-8") as info_file:
        rows = info_file.readlines()

    for row in rows:
        columns = row.split()
        if not columns or columns[0] != "|" or columns[-1] != "|":
            continue

        if len(columns) == 8 and _is_number(columns[2]) and _is_number(
                columns[5]):
            info[columns[1]] = entry_counter
            units[columns[1]] = columns[3]
            entry_counter += 1

            info[columns[4]] = entry_counter
            units[columns[4]] = columns[6]
            entry_counter += 1
            continue

        if len(columns) == 5 and _is_number(columns[2]):
            info[columns[1]] = entry_counter
            units[columns[1]] = columns[3]
            entry_counter += 1
            has_single_column_row = True
            continue

        if "info file" in row:
            continue

        return None

    if not has_single_column_row:
        return None

    return info, units


def _is_number(value):
    try:
        float(value)
    except ValueError:
        return False

    return True
