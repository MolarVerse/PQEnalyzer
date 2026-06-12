import subprocess
import sys
from pathlib import Path


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


def test_cli_help_mentions_gui_and_tui_modes():
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
    assert "{gui,tui}" in result.stdout


def test_gui_mode_logs_reader_validation_errors():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            "tests/data/md-01.en",
            "tests/data/md-02.en",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "ERROR: The energy files do not have the same info parameters" in (
        result.stderr)


def test_tui_mode_does_not_duplicate_upstream_reader_errors():
    project_root = Path(__file__).resolve().parents[1]
    missing_file = "tests/data/does-not-exist.en"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "tui",
            missing_file,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert result.stderr.count(f"File {missing_file} not found.") == 1


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


def test_cli_requires_app_mode():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "examples/md-01.en"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "invalid choice" in result.stderr
