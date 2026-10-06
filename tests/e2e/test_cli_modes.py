import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_FILE = PROJECT_ROOT / "examples" / "md-02.en"
BOX_EXAMPLE_FILE = PROJECT_ROOT / "examples" / "box-01.box"
SINGLE_COLUMN_EXAMPLE_FILE = (
    PROJECT_ROOT / "tests" / "data" / "single-column-output.en"
)
OPTIMIZER_EXAMPLE_FILE = PROJECT_ROOT / "examples" / "optimization.opt"


def _subprocess_environment():
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    env.setdefault(
        "PQENALYZER_CONFIG_DIR",
        str(Path(tempfile.gettempdir()) / f"pqenalyzer-tests-{os.getpid()}"),
    )
    return env


def _terminate_process(process):
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _read_lines(stream, count, timeout=8.0):
    """Read a fixed startup block without hanging a failed GUI test."""
    lines = []

    def read():
        for _ in range(count):
            lines.append(stream.readline().rstrip("\n"))

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(timeout)
    if reader.is_alive():
        pytest.fail("Timed out waiting for desktop startup output.")
    return lines


@pytest.mark.e2e
@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(["gui"], id="explicit-gui"),
        pytest.param([], id="default-gui"),
    ],
)
def test_gui_mode_announces_ready_dataset_and_closes_cleanly(mode):
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", *mode, str(EXAMPLE_FILE)],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        assert process.stdout is not None
        output = _read_lines(process.stdout, 3)
        assert output == [
            "PQEnalyzer  Desktop",
            "Data   5,000 rows / 1 file",
            "Stop   Close window / Ctrl+C",
        ]
        assert process.poll() is None

        process.send_signal(signal.SIGINT)
        stdout_tail, stderr = process.communicate(timeout=8)
        assert stdout_tail == ""
        assert process.returncode == 0
        assert stderr.count("Desktop ready.") == 1
        assert stderr.count("Desktop closed.") == 1
        assert "Detected PQ energy input" not in stderr
        assert "Traceback" not in stderr
        assert "TclError" not in stderr
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_gui_mode_starts_with_box_file_and_can_be_terminated():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            str(BOX_EXAMPLE_FILE),
        ],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(2)

        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            pytest.fail(
                "GUI box mode exited before the startup smoke window elapsed.\n"
                f"returncode={process.returncode}\n"
                f"stdout={stdout}\n"
                f"stderr={stderr}")
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_gui_mode_starts_with_single_column_info():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            str(SINGLE_COLUMN_EXAMPLE_FILE),
        ],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(2)

        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            pytest.fail(
                "GUI mode exited while opening single-column PQ info.\n"
                f"returncode={process.returncode}\n"
                f"stdout={stdout}\n"
                f"stderr={stderr}"
            )
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_gui_mode_starts_with_optimizer_file_and_can_be_terminated():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "gui",
            str(OPTIMIZER_EXAMPLE_FILE),
        ],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(2)

        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            pytest.fail(
                "Optimizer GUI mode exited before the startup smoke window "
                "elapsed.\n"
                f"returncode={process.returncode}\n"
                f"stdout={stdout}\n"
                f"stderr={stderr}")
    finally:
        _terminate_process(process)
