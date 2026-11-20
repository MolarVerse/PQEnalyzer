"""
Column names and units from the PQ ``.en`` header.

PQ energy files may start with ``# PQ energy file <version>`` followed by one
``NAME[unit]`` token per column. Released PQAnalysis versions skip these
comment lines but still take names only from ``.info``; this module fills that
gap until PQAnalysis reads the header itself.
"""

import re


PQ_HEADER_PREFIX = "# PQ energy file"

_COLUMN_PATTERN = re.compile(r"^(?P<name>[^\[\]]+)\[(?P<unit>[^\[\]]*)\]$")


class EnergyHeaderError(ValueError):
    """
    Raised when a PQ energy file header cannot be parsed.
    """


def has_pq_header(filename) -> bool:
    """
    Return whether an energy file starts with the PQ energy file header.
    """

    lines = _read_header_lines(filename, 1)
    return bool(lines) and lines[0].startswith(PQ_HEADER_PREFIX)


def read_pq_header(filename):
    """
    Return ``(info, units)`` dictionaries from a PQ energy file header.

    ``info`` maps each column name to its column index and ``units`` maps it
    to its unit, matching the dictionaries PQAnalysis builds from ``.info``.
    """

    lines = _read_header_lines(filename, 2)
    if len(lines) < 2 or not lines[0].startswith(PQ_HEADER_PREFIX):
        raise EnergyHeaderError(
            f"{filename} does not start with a PQ energy file header.")

    column_line = lines[1].strip()
    if not column_line.startswith("#"):
        raise EnergyHeaderError(
            f"{filename}: the second header line must list the columns.")

    info = {}
    units = {}
    for index, token in enumerate(column_line[1:].split()):
        match = _COLUMN_PATTERN.match(token)
        if match is None:
            raise EnergyHeaderError(
                f"{filename}: invalid header column '{token}', "
                "expected NAME[unit].")

        name = match.group("name")
        if name in info:
            raise EnergyHeaderError(
                f"{filename}: duplicate header column '{name}'.")

        info[name] = index
        units[name] = match.group("unit")

    if not info:
        raise EnergyHeaderError(f"{filename}: the header lists no columns.")

    return info, units


def _read_header_lines(filename, count):
    """
    Return up to ``count`` leading lines, or an empty list if unreadable.
    """

    try:
        with open(filename, "r", encoding="utf-8",
                  errors="replace") as energy_file:
            lines = []
            for line in energy_file:
                lines.append(line.rstrip("\n"))
                if len(lines) == count:
                    break
            return lines
    except OSError:
        return []
