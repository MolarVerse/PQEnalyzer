import subprocess
import sys
from pathlib import Path

import pytest


def test_cli_version_from_source_checkout():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "--version"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert result.stdout.startswith("PQEnalyzer ")


def test_cli_help_mentions_web_and_gui_modes():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "usage: pqenalyzer [-h] [-v] [gui|web] ..." in (
        " ".join(result.stdout.lower().split())
    )
    assert "{gui,web}" not in result.stdout
    assert "[gui|web]" in result.stdout
    assert "gui" in result.stdout
    assert "web" in result.stdout
    assert "\033[" not in result.stdout


def test_web_help_in_a_terminal_is_branded_and_shows_defaults(monkeypatch):
    """Interactive help identifies the app and its usable server defaults."""
    import io
    import re

    from PQEnalyzer.__main__ import main

    class Terminal(io.StringIO):
        def isatty(self):
            return True

    stream = Terminal()
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "argv", ["pqenalyzer", "web", "--help"])
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setenv("COLUMNS", "48")
    monkeypatch.delenv("NO_COLOR", raising=False)

    with pytest.raises(SystemExit) as exited:
        main()

    assert exited.value.code == 0
    output = stream.getvalue()
    plain = re.sub(r"\033\[[0-9;]*m", "", output)
    assert "PQEnalyzer" in plain
    assert "--no-open" in plain
    assert "--log-level" in plain
    assert "127.0.0.1" in plain
    assert "8766" in plain
    assert "info" in plain
    assert "\033[" in output


def test_web_mode_rejects_non_loopback_host():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "web",
            "--host",
            "0.0.0.0",
            "--port",
            "8799",
            "examples/md-01.en",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--host must be a loopback address" in result.stderr


def test_web_mode_reports_an_occupied_port_without_announcing_startup():
    import socket

    project_root = Path(__file__).resolve().parents[1]
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        port = occupied.getsockname()[1]
        result = subprocess.run(
            [sys.executable, "-m", "PQEnalyzer", "web", "--no-open",
             "--port", str(port), "tests/data/md-01.en"],
            cwd=project_root, capture_output=True, text=True, timeout=20,
        )

    assert result.returncode != 0
    assert "address already in use" in result.stderr.lower()
    assert "--port" in result.stderr
    assert "Traceback" not in result.stderr
    assert "PQEnalyzer  Web" not in result.stdout
    assert "Open   http" not in result.stdout


def test_gui_help_mentions_optimizer_input():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "gui", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--opt" in result.stdout
    assert "optimizer output" in result.stdout
    assert "--log-level" in result.stdout
    assert "info" in result.stdout


def test_default_gui_mode_logs_reader_errors():
    project_root = Path(__file__).resolve().parents[1]
    missing_file = "tests/data/does-not-exist.en"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            missing_file,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert f"File {missing_file} not found." in result.stderr


def test_explicit_gui_mode_still_logs_reader_errors():
    project_root = Path(__file__).resolve().parents[1]
    missing_file = "tests/data/does-not-exist.en"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            missing_file,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert f"File {missing_file} not found." in result.stderr


def test_cli_rejects_multiple_forced_input_formats():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            "--box",
            "--qmcfc",
            "examples/box-01.box",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "not allowed with argument" in result.stderr


def test_cli_defaults_to_gui_mode():
    project_root = Path(__file__).resolve().parents[1]
    missing_file = "tests/data/does-not-exist.en"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            missing_file,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "invalid choice" not in result.stderr
    assert f"File {missing_file} not found." in result.stderr


def test_default_gui_mode_accepts_input_format_flags():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--box",
            "--qmcfc",
            "examples/box-01.box",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "not allowed with argument" in result.stderr
