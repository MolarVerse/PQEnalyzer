import os
import subprocess
import sys
import tempfile
from pathlib import Path


def complete_cli(command_line):
    """
    Run argcomplete against the source checkout and return completions.
    """

    project_root = Path(__file__).resolve().parents[1]

    with tempfile.NamedTemporaryFile() as output:
        result = subprocess.run(
            [sys.executable, "-m", "PQEnalyzer"],
            cwd=project_root,
            env={
                **dict(os.environ),
                "_ARGCOMPLETE": "1",
                "_ARGCOMPLETE_STDOUT_FILENAME": output.name,
                "_ARGCOMPLETE_SHELL": "bash",
                "COMP_LINE": command_line,
                "COMP_POINT": str(len(command_line)),
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        output.seek(0)
        completions = output.read().decode("utf-8")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    return [completion.rstrip() for completion in completions.split("\013")]


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


def test_cli_help_mentions_completion_command():
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
    assert "pqenalyzer completion {bash,zsh,fish}" in result.stdout


def test_cli_logs_reader_validation_errors():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
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


def test_cli_does_not_duplicate_upstream_reader_errors():
    project_root = Path(__file__).resolve().parents[1]
    missing_file = "tests/data/does-not-exist.en"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
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


def test_cli_module_has_argcomplete_marker():
    project_root = Path(__file__).resolve().parents[1]
    module_head = (project_root / "PQEnalyzer" /
                   "__main__.py").read_text(encoding="utf-8")[:1024]

    assert "PYTHON_ARGCOMPLETE_OK" in module_head


def test_cli_prints_bash_completion_script():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "completion", "bash"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "_ARGCOMPLETE=1" in result.stdout
    assert "complete " in result.stdout
    assert "pqenalyzer" in result.stdout


def test_cli_prints_zsh_completion_script():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "completion", "zsh"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "#compdef pqenalyzer" in result.stdout
    assert '_ARGCOMPLETE_SHELL="zsh"' in result.stdout


def test_cli_prints_fish_completion_script():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "completion", "fish"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "function __fish_pqenalyzer_complete" in result.stdout
    assert "complete --command pqenalyzer" in result.stdout


def test_cli_rejects_unknown_completion_shell():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "completion", "powershell"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "invalid choice: 'powershell'" in result.stderr


def test_cli_rejects_multiple_forced_input_formats():
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
    assert "--pq, --qmcfc, and --box are mutually exclusive." in (
        result.stderr)


def test_cli_no_gui_plot_exits_without_prompt():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
            "--plot",
            "TEMPERATURE",
            "examples/md-01.en",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "Select the information parameter" not in result.stdout
    assert "TEMPERATURE / K" in result.stdout
    assert "Simulation Time" in result.stdout


def test_cli_no_gui_summary_prints_loaded_input_details():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
            "--summary",
            "examples/box-01.box",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "PQEnalyzer input summary" in result.stdout
    assert "examples/box-01.box: 5 rows" in result.stdout
    assert "BOX-X [A]" in result.stdout
    assert "BOX-VOLUME [A^3]" in result.stdout


def test_cli_diff_requires_two_input_files():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
            "--plot",
            "TEMPERATURE",
            "--diff",
            "examples/md-01.en",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "--diff requires exactly two input files." in result.stderr


def test_cli_plot_parameter_completion_uses_common_defaults():
    completions = complete_cli("pqenalyzer --no-gui --plot T")

    assert completions == ["TEMPERATURE"]


def test_cli_plot_parameter_completion_uses_detected_box_parameters():
    completions = complete_cli(
        "pqenalyzer --no-gui examples/box-01.box --plot B")

    assert "BOX-X" in completions
    assert "BOX-VOLUME" in completions
    assert "BETA" in completions
    assert "TEMPERATURE" not in completions
