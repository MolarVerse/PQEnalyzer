import os
import subprocess
import sys
import tempfile
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


@pytest.mark.e2e
def test_gui_mode_starts_and_can_be_terminated():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", "gui", str(EXAMPLE_FILE)],
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
                "GUI mode exited before the startup smoke window elapsed.\n"
                f"returncode={process.returncode}\n"
                f"stdout={stdout}\n"
                f"stderr={stderr}")
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_default_gui_mode_starts_and_can_be_terminated():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("GUI e2e test requires a display; run with xvfb-run.")

    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", str(EXAMPLE_FILE)],
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
                "Default GUI mode exited before the startup smoke window "
                "elapsed.\n"
                f"returncode={process.returncode}\n"
                f"stdout={stdout}\n"
                f"stderr={stderr}")
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
