"""
This is the main file of the PQEnalyzer project.
"""

import argparse

from .__version__ import __version__
from .app import App

def main():
    """
    The main function of the PQEnalyzer project.
    """

    parser = argparse.ArgumentParser(description="PQEnalyzer - MolarVerse")
    parser.add_argument("filenames", metavar="filename", nargs="+", help="The name of the energy files to read the data from.")
    parser.add_argument("--version", "-v", action="version", version=f"PQEnalyzer {__version__}")
    
    filenames = parser.parse_args().filenames

    app = App(filenames)
    app.mainloop()

if __name__ == "__main__":
    main()