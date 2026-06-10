import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_FILE = PROJECT_ROOT / "examples" / "md-02.en"
BOX_EXAMPLE_FILE = PROJECT_ROOT / "examples" / "box-01.box"


def _subprocess_environment():
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    env.setdefault("COLUMNS", "100")
    env.setdefault("LINES", "40")
    return env


def _read_until(fd, expected, *, timeout):
    deadline = time.monotonic() + timeout
    output = bytearray()

    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        readable, _, _ = select.select([fd], [], [], min(0.1, remaining))

        if fd not in readable:
            continue

        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break

        if not chunk:
            break

        output.extend(chunk)
        if expected in output:
            return bytes(output)

    decoded_output = bytes(output).decode(errors="replace")
    pytest.fail(f"Timed out waiting for {expected!r}.\nOutput:\n{decoded_output}")


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
                "GUI mode exited before the startup smoke window elapsed.\n"
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
            "--box",
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
def test_no_gui_mode_renders_terminal_plot_and_exits():
    master_fd, slave_fd = os.openpty()
    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", "--no-gui", str(EXAMPLE_FILE)],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)

    try:
        _read_until(master_fd,
                    b"Select the information parameter to plot",
                    timeout=10)
        os.write(master_fd, b"\r")

        plot_output = _read_until(master_fd,
                                  b"Do you want to exit?",
                                  timeout=10)
        assert b"TEMPERATURE / K" in plot_output
        assert b"Simulation Time" in plot_output

        os.write(master_fd, b"y\r")
        process.wait(timeout=10)

        assert process.returncode == 0
    finally:
        os.close(master_fd)
        _terminate_process(process)


@pytest.mark.e2e
def test_no_gui_mode_renders_box_plot_and_exits():
    master_fd, slave_fd = os.openpty()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "--no-gui",
            "--box",
            str(BOX_EXAMPLE_FILE),
        ],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)

    try:
        _read_until(master_fd,
                    b"Select the information parameter to plot",
                    timeout=10)
        os.write(master_fd, b"\r")

        plot_output = _read_until(master_fd,
                                  b"Do you want to exit?",
                                  timeout=10)
        assert b"BOX-X / A" in plot_output
        assert b"Simulation Time" in plot_output

        os.write(master_fd, b"y\r")
        process.wait(timeout=10)

        assert process.returncode == 0
    finally:
        os.close(master_fd)
        _terminate_process(process)
