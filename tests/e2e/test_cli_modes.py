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


def _wait_for_exit(process, fd, *, timeout):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if process.poll() is not None:
            return

        remaining = deadline - time.monotonic()
        readable, _, _ = select.select([fd], [], [], min(0.1, remaining))
        if fd in readable:
            try:
                os.read(fd, 8192)
            except OSError:
                break

    if process.poll() is not None:
        return

    process.wait(timeout=1)


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
def test_tui_mode_opens_dashboard_and_chart_views():
    master_fd, slave_fd = os.openpty()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "tui",
            str(EXAMPLE_FILE),
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
        dashboard_output = _read_until(master_fd,
                                       b"TEMPERATURE",
                                       timeout=10)
        assert b"Rows" in dashboard_output

        os.write(master_fd, b"\r")
        chart_output = _read_until(master_fd,
                                   b"Simulation Time",
                                   timeout=10)
        assert b"TEMPERATURE / K" in chart_output

        os.write(master_fd, b"\x1b")
        dashboard_output = _read_until(master_fd,
                                       b"Parameter",
                                       timeout=10)
        assert b"TEMPERATURE" in dashboard_output

        os.write(master_fd, b"q")
        _wait_for_exit(process, master_fd, timeout=10)

        assert process.returncode == 0
    finally:
        os.close(master_fd)
        _terminate_process(process)


@pytest.mark.e2e
def test_tui_mode_starts_with_box_file_and_can_be_quit():
    master_fd, slave_fd = os.openpty()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "tui",
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
        dashboard_output = _read_until(master_fd,
                                       b"BOX-VOLUME",
                                       timeout=10)
        assert b"BOX-X" in dashboard_output

        os.write(master_fd, b"q")
        _wait_for_exit(process, master_fd, timeout=10)

        assert process.returncode == 0
    finally:
        os.close(master_fd)
        _terminate_process(process)
