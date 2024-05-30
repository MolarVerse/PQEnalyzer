"""
This is the main module of the package. It is used to import the
main classes and functions of the package.
"""
import sys

# beartype
from beartype.claw import beartype_this_package

beartype_this_package()

# zero traceback limit
# sys.tracebacklimit = 0

# base path
__base__ = __file__.split("/__init__.py")[0]
