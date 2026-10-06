"""Shared terminal presentation for the PQ applications.

Vendor this file unchanged with the design tokens. Requires Rich and rich-argparse.
"""

import argparse
from functools import partial
import logging
import os
import shutil
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme
from rich_argparse import RichHelpFormatter


WORDMARKS = {
    'PQSetup': (
        '    ____  ____   _____      __',
        '   / __ \\/ __ \\ / ___/___  / /___  ______',
        '  / /_/ / / / / \\__ \\/ _ \\/ __/ / / / __ \\',
        ' / ____/ /_/ / ___/ /  __/ /_/ /_/ / /_/ /',
        '/_/    \\___\\_\\/____/\\___/\\__/\\__,_/ .___/',
        '                                 /_/',
    ),
    'PQViewer': (
        '    ____  ____ _    ___',
        '   / __ \\/ __ \\ |  / (_)__ _      _____  _____',
        '  / /_/ / / / / | / / / _ \\ | /| / / _ \\/ ___/',
        ' / ____/ /_/ /| |/ / /  __/ |/ |/ /  __/ /',
        '/_/    \\___\\_\\|___/_/\\___/|__/|__/\\___/_/',
    ),
    'PQEnalyzer': (
        '    ____  ____    ______            __',
        '   / __ \\/ __ \\  / ____/___  ____ _/ /_  ______  ___  _____',
        '  / /_/ / / / / / __/ / __ \\/ __ `/ / / / /_  / / _ \\/ ___/',
        ' / ____/ /_/ / / /___/ / / / /_/ / / /_/ / / /_/  __/ /',
        '/_/    \\___\\_\\/_____/_/ /_/\\__,_/_/\\__, / /___/\\___/_/',
        '                                  /____/',
    ),
}


class Terminal:
    """App identity and an independent event logger; no global logging changes."""

    def __init__(self, name, version, colors):
        self.name = name
        self.version = version
        self.colors = colors
        # PQAnalysis can replace logging's global logger class with one whose
        # error method raises. Application events must not change control flow.
        self.log = logging.Logger(name)
        self.log.addHandler(logging.NullHandler())
        self.log.propagate = False

    def _console(self, stream):
        interactive = (
            getattr(stream, "isatty", lambda: False)()
            and os.environ.get("TERM", "").lower() != "dumb"
        )
        color = interactive and "NO_COLOR" not in os.environ
        return Console(
            file=stream,
            width=min(shutil.get_terminal_size().columns, 80),
            force_terminal=interactive,
            color_system="truecolor" if color else None,
            highlight=False,
            theme=Theme({
                "logging.level.debug": "dim",
                "logging.level.info": self.colors["accent"],
                "logging.level.warning": self.colors["warning"],
                "logging.level.error": self.colors["danger"],
                "logging.level.critical": f"bold {self.colors['danger']}",
            }),
        )

    def configure_logging(self, level="info"):
        """Replace only this app's handler; repeated configuration is safe."""
        self.log.handlers.clear()
        self.log.setLevel(level.upper())
        console = self._console(sys.stderr)
        if console.is_terminal:
            handler = RichHandler(
                console=console,
                log_time_format="%H:%M:%S",
                omit_repeated_times=False,
                show_path=False,
                markup=False,
                highlighter=None,
            )
        else:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S",
            ))
        self.log.addHandler(handler)

    def _header(self, console, mode=""):
        console.print()
        wordmark = WORDMARKS.get(self.name, ())
        if wordmark and max(map(len, wordmark)) + 2 <= console.width:
            console.print(
                Text("\n".join(f"  {line}" for line in wordmark)),
                style=f"bold {self.colors['accent']}",
            )
            console.print()
        console.print(Text.assemble(
            (f"  {self.name}", "bold"),
            (f"  {self.version}", "dim"),
            (f"  {mode}" if mode else "", "dim"),
        ))
        console.rule(style="dim")

    def startup(self, url, details=()):
        """Present a server that is already ready, with optional app facts."""
        self._status("Web", url, details, "Ctrl+C")

    def desktop(self, details=()):
        """Present a desktop window that is already ready."""
        self._status("Desktop", None, details, "Close window / Ctrl+C")

    def _status(self, mode, url, details, stop):
        console = self._console(sys.stdout)
        if not console.is_terminal:
            lines = [f"{self.name}  {mode}"]
            lines.extend(f"{label:<7}{value}" for label, value in details)
            if url:
                lines.append(f"Open   {url}")
            lines.append(f"Stop   {stop}")
            print("\n".join(lines), flush=True)
            return

        self._header(console, mode)
        console.print()
        if console.width >= 48:
            if url:
                console.print(Text.assemble(
                    ("  Browser   ", "dim"),
                    (url, f"bold {self.colors['accent']}"),
                ))
            for label, value in details:
                console.print(Text.assemble((f"  {label:<8}  ", "dim"), str(value)))
        else:
            if url:
                console.print(Text(url, style=f"bold {self.colors['accent']}"))
            for _label, value in details:
                console.print(Text(str(value)))
        console.print()
        console.print(Text.assemble((f"  {stop}", "bold"), (" to stop", "dim")))
        console.print()
        sys.stdout.flush()

    def argument_parser(self, *args, **kwargs):
        """Build argparse help with this app's identity and shared colors."""
        return _Parser(*args, terminal=self, **kwargs)

    def _formatter(self, prog, stream):
        console = self._console(stream)
        formatter = RichHelpFormatter(prog, console=console, width=console.width - 2)
        formatter.styles = {
            **RichHelpFormatter.styles,
            "argparse.args": self.colors["accent"],
            "argparse.groups": "bold",
            "argparse.metavar": "default",
            "argparse.prog": self.colors["accent"],
        }
        return formatter


class _Parser(argparse.ArgumentParser):
    def __init__(self, *args, terminal, **kwargs):
        self._terminal = terminal
        self._output_stream = None
        super().__init__(*args, **kwargs)

    def _get_formatter(self):
        stream = self._output_stream if self._output_stream is not None else sys.stdout
        return self._terminal._formatter(self.prog, stream)

    def add_subparsers(self, **kwargs):
        kwargs.setdefault("parser_class", partial(_Parser, terminal=self._terminal))
        return super().add_subparsers(**kwargs)

    def print_help(self, file=None):
        stream = file if file is not None else sys.stdout
        previous, self._output_stream = self._output_stream, stream
        try:
            console = self._terminal._console(stream)
            if console.is_terminal:
                self._terminal._header(console)
                console.print()
            super().print_help(file=stream)
        finally:
            self._output_stream = previous

    def print_usage(self, file=None):
        stream = file if file is not None else sys.stdout
        previous, self._output_stream = self._output_stream, stream
        try:
            super().print_usage(file=stream)
        finally:
            self._output_stream = previous
