"""
This is the main file of the PQEnalyzer project. It contains the
main function that is executed when the program is run.
"""

import sys
import argparse
import argcomplete
from PQAnalysis.traj import MDEngineFormat

from .__version__ import __version__
from .apps import App, TermApp
from .readers import Reader


def main():
    """
    The main function of the PQEnalyzer project. It reads the data
    from the energy files and plots the data in the GUI or in the terminal.
    Use the -h or --help flag to see the command line arguments.

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
        metavar="filenames",
        nargs="+",
        help="The name of the energy files to read the data from.")
    parser.add_argument("-q",
                        "--qmcfc",
                        action="store_true",
                        help="Use the QMCFC output as input.")
    parser.add_argument("-n",
                        "--no-gui",
                        action="store_true",
                        help="Opens the terminal plotting feature.")
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    # autocomplete the command line arguments
    argcomplete.autocomplete(parser)

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

    # if the user wants to use the terminal plotting feature
    if parser.parse_args().no_gui:
        # create the termplot
        termapp = TermApp(reader)
        termapp.start()
    else:
        # create the app
        app = App(reader)
        app.build()
        app.mainloop()

    return None


if __name__ == "__main__":
    main()
