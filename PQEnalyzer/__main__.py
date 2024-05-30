"""
This is the main file of the PQEnalyzer project. It contains the
main function that is executed when the program is run.
"""

import signal
import sys
import argparse
from PQAnalysis.traj import MDEngineFormat

from .__version__ import __version__
from .gui import App
from .readers import Reader


def main():
    """
    The main function of the PQEnalyzer project.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    # parse command line arguments
    parser = argparse.ArgumentParser(description="PQEnalyzer - MolarVerse")
    parser.add_argument(
        "filenames",
        metavar="filename",
        nargs="+",
        help="The name of the energy files to read the data from.")
    parser.add_argument("-q",
                        "--qmcfc",
                        action="store_true",
                        help="Use the QMCFC output as input.")
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    # get command line arguments
    filenames = parser.parse_args().filenames

    # set the md format
    md_format = MDEngineFormat.PQ

    # if the user wants to use the QMCFC output as input
    if parser.parse_args().qmcfc:
        md_format = MDEngineFormat.QMCFC  # set the md format to QMCFC

    # create the reader
    try:
        reader = Reader(filenames, md_format)
    except Exception as e:
        print(e)
        sys.exit(1)

    # create the app
    app = App(reader)
    app.build()
    app.mainloop()

    return None


if __name__ == "__main__":
    main()
