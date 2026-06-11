"""
Command-line entrypoint for PQEnalyzer.

The CLI reads one or more data files through a PQAnalysis-backed reader and
then starts either the graphical CustomTkinter application or the terminal
plotting flow. GUI imports stay inside main() so terminal mode can start
without loading Tkinter.
"""

# PYTHON_ARGCOMPLETE_OK

import sys
import argparse
import argcomplete

from . import __version__
from ._logging import configure_logging, get_logger


logger = get_logger(__name__)


PLOT_PARAMETER_COMPLETIONS = (
    "TEMPERATURE",
    "PRESSURE",
    "E(TOT)",
    "E(QM)",
    "N(QM-ATOMS)",
    "E(KIN)",
    "E(INTRA)",
    "VOLUME",
    "DENSITY",
    "MOMENTUM",
    "LOOPTIME",
    "BOX-X",
    "BOX-Y",
    "BOX-Z",
    "ALPHA",
    "BETA",
    "GAMMA",
    "BOX-VOLUME",
)
COMPLETION_SHELLS = ("bash", "zsh", "fish")


def _handle_completion_command(argv):
    """
    Print a shell completion script for package-manager installation.
    """

    if len(argv) <= 1 or argv[1] != "completion":
        return False

    parser = argparse.ArgumentParser(
        prog="pqenalyzer completion",
        description="Print shell completion code for pqenalyzer.",
    )
    parser.add_argument("shell", choices=COMPLETION_SHELLS)
    args = parser.parse_args(argv[2:])

    sys.stdout.write(argcomplete.shellcode(["pqenalyzer"], shell=args.shell))
    return True


def _completion_matches(parameters, prefix):
    """
    Return case-insensitive parameter completions for argcomplete.
    """

    normalized_prefix = prefix.casefold()
    return [
        parameter for parameter in parameters
        if parameter.casefold().startswith(normalized_prefix)
    ]


def _detect_completion_parameters(parsed_args):
    """
    Return parameters from the currently supplied input files, if readable.
    """

    filenames = getattr(parsed_args, "filenames", None) or []
    if not filenames:
        return []

    forced_formats = [
        getattr(parsed_args, "pq", False),
        getattr(parsed_args, "qmcfc", False),
        getattr(parsed_args, "box", False),
    ]
    if sum(forced_formats) > 1:
        return []

    input_format = "auto"
    if getattr(parsed_args, "pq", False):
        input_format = "pq"
    elif getattr(parsed_args, "qmcfc", False):
        input_format = "qmcfc"
    elif getattr(parsed_args, "box", False):
        input_format = "box"

    previous_disable_level = None
    try:
        import logging

        from .readers import create_reader

        previous_disable_level = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        reader = create_reader(filenames, input_format=input_format)
    except Exception:  # pylint: disable=broad-exception-caught
        return []
    finally:
        if previous_disable_level is not None:
            logging.disable(previous_disable_level)

    return [*reader.energies[0].info][1:]


def _complete_plot_parameter(prefix, parsed_args, **kwargs):
    """
    Complete --plot with detected parameters or common PQ/box defaults.
    """

    parameters = _detect_completion_parameters(parsed_args)
    if not parameters:
        parameters = PLOT_PARAMETER_COMPLETIONS

    return _completion_matches(parameters, prefix)


def _completion_validator(completion, prefix):
    """
    Let parameter completions match case-insensitively.
    """

    return completion.casefold().startswith(prefix.casefold())


def main():
    """
    Parse command-line arguments, read input files, and start the chosen UI.

    PQAnalysis exceptions are allowed to keep their own formatting. Other
    reader errors are logged through the application logger before returning a
    non-zero process exit.
    """
    if _handle_completion_command(sys.argv):
        return None

    parser = argparse.ArgumentParser(
        description="PQEnalyzer - MolarVerse",
        epilog="Shell completion: pqenalyzer completion {bash,zsh,fish}",
    )
    parser.add_argument(
        "filenames",
        metavar="filenames",
        nargs="+",
        help="The name of the files to read the data from.")
    parser.add_argument("--pq",
                        action="store_true",
                        help="Force PQ energy input.")
    parser.add_argument("-q",
                        "--qmcfc",
                        action="store_true",
                        help="Use the QMCFC output as input.")
    parser.add_argument("--box",
                        action="store_true",
                        help="Read PQ box files instead of energy files.")
    parser.add_argument("-n",
                        "--no-gui",
                        action="store_true",
                        help="Opens the terminal plotting feature.")
    plot_argument = parser.add_argument(
        "--plot",
        metavar="PARAMETER",
        help="Plot one parameter in no-GUI mode and exit.")
    plot_argument.completer = _complete_plot_parameter
    parser.add_argument("--diff",
                        action="store_true",
                        help="Plot the first input file minus the second.")
    parser.add_argument("--summary",
                        action="store_true",
                        help="Print an input summary in no-GUI mode and exit.")
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    argcomplete.autocomplete(parser, validator=_completion_validator)

    args = parser.parse_args()
    configure_logging()

    if args.plot and not args.no_gui:
        parser.error("--plot requires --no-gui.")

    if args.diff and not args.plot:
        parser.error("--diff requires --plot.")

    if args.summary and not args.no_gui:
        parser.error("--summary requires --no-gui.")

    if args.summary and args.plot:
        parser.error("--summary and --plot are mutually exclusive.")

    from .readers import create_reader

    forced_formats = [args.pq, args.qmcfc, args.box]
    if sum(forced_formats) > 1:
        parser.error("--pq, --qmcfc, and --box are mutually exclusive.")

    input_format = "auto"
    if args.pq:
        input_format = "pq"
    elif args.qmcfc:
        input_format = "qmcfc"
    elif args.box:
        input_format = "box"

    try:
        reader = create_reader(args.filenames, input_format=input_format)
    except Exception as e:
        if not e.__class__.__module__.startswith("PQAnalysis"):
            logger.error("%s", e)
        sys.exit(1)

    if args.no_gui:
        from .apps import TermApp

        termapp = TermApp(reader)
        try:
            if args.summary:
                print(termapp.summary())
            elif args.plot:
                if args.diff and len(reader.energies) != 2:
                    parser.error("--diff requires exactly two input files.")
                termapp.plot(args.plot, difference=args.diff)
            else:
                termapp.start()
        except ValueError as error:
            logger.error("%s", error)
            sys.exit(1)
    else:
        from .apps import App

        app = App(reader)
        app.build()
        app.mainloop()

    return None


if __name__ == "__main__":
    main()
