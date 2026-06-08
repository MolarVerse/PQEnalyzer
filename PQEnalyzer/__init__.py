"""
This is the main module of the package. It is used to import the
main classes and functions of the package.
"""
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# beartype
from beartype.claw import beartype_this_package

beartype_this_package()

# zero traceback limit
# sys.tracebacklimit = 0

# base path
__base__ = str(Path(__file__).resolve().parent)


def _version_from_git():
    import subprocess

    result = subprocess.run(
        ["git", "describe", "--tags", "--dirty", "--always"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        return result.stdout.strip() or None

    return None


def _get_version():
    try:
        return version("PQEnalyzer")
    except PackageNotFoundError:
        pass

    try:
        from setuptools_scm import get_version

        return get_version(root="..", relative_to=__file__)
    except Exception:
        pass

    try:
        git_version = _version_from_git()
    except Exception:
        git_version = None

    return git_version or "0+unknown"


__version__ = _get_version()
