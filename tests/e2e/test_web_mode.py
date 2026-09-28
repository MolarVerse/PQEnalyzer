import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_FILE = PROJECT_ROOT / "examples" / "md-02.en"


def _subprocess_environment():
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    env.setdefault(
        "PQENALYZER_CONFIG_DIR",
        str(Path(tempfile.gettempdir()) / f"pqenalyzer-tests-{os.getpid()}"),
    )
    return env


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_status(port, timeout=25.0):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/status", timeout=2
            ) as response:
                return json.load(response)
        except OSError as error:
            last_error = error
            time.sleep(0.25)
    pytest.fail(f"Timed out waiting for web status. Last error: {last_error}")


def _wait_for_hello(port, timeout=10.0):
    deadline = time.monotonic() + timeout
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/events", timeout=timeout + 5
        ) as response:
            while time.monotonic() < deadline:
                line = response.fp.readline().decode(errors="replace")
                if line.startswith("event: hello"):
                    return True
    except OSError as error:
        pytest.fail(f"Event stream failed: {error}")
    pytest.fail("Timed out waiting for the SSE hello event.")


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
def test_web_mode_serves_status_and_events():
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "web",
            "--no-open",
            "--port",
            str(port),
            str(EXAMPLE_FILE),
        ],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        status = _wait_for_status(port)
        assert status["stale"] is False
        assert sum(item["rows"] for item in status["files"]) > 0
        assert _wait_for_hello(port)
    finally:
        _terminate_process(process)
