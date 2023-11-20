"""
This is the main file of the PQEnalyzer project.
"""

import argparse
from PQAnalysis.traj.formats import MDEngineFormat

from .__version__ import __version__
from .classes.app import App
from .classes.reader import Reader

def main():
    """
    The main function of the PQEnalyzer project.
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description="PQEnalyzer - MolarVerse")
    parser.add_argument("filenames", metavar="filename", nargs="+", help="The name of the energy files to read the data from.")
    parser.add_argument("-q", "--qmcfc", action="store_true", help="Use the QMCFC output as input.")
    parser.add_argument("-v", "--version", action="version", version=f"PQEnalyzer {__version__}")
    
    # get command line arguments
    filenames = parser.parse_args().filenames
    
    # set the md format
    md_format = MDEngineFormat.PIMD_QMCF
    if parser.parse_args().qmcfc: # if the user wants to use the QMCFC output as input
        md_format = MDEngineFormat.QMCFC # set the md format to QMCFC

    # create the reader
    try:
        reader = Reader(filenames, md_format)
    except ValueError as e:
        print(e)
        exit(1)

    app = App(reader)
    app.mainloop()

if __name__ == "__main__":
    main()