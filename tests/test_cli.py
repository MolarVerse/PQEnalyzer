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
    assert "gui" in result.stdout
    assert "tui" in result.stdout


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
