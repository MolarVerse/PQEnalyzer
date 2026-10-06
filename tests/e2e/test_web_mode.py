import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


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


def _free_port(host="127.0.0.1", family=socket.AF_INET):
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.bind((host, 0))
            return sock.getsockname()[1]
    except OSError as error:
        if family == socket.AF_INET6:
            pytest.skip(f"IPv6 loopback is unavailable: {error}")
        raise


def _web_url(host, port):
    url_host = f"[{host}]" if ":" in host else host
    return f"http://{url_host}:{port}"


def _open_url(url, timeout):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(url, timeout=timeout)


def _wait_for_status(port, timeout=25.0, host="127.0.0.1"):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with _open_url(f"{_web_url(host, port)}/api/status", timeout=2) as response:
                return json.load(response)
        except OSError as error:
            last_error = error
            time.sleep(0.25)
    pytest.fail(f"Timed out waiting for web status. Last error: {last_error}")


def _wait_for_hello(port, timeout=10.0, host="127.0.0.1"):
    deadline = time.monotonic() + timeout
    try:
        with _open_url(
            f"{_web_url(host, port)}/api/events", timeout=timeout + 5
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


def _read_lines(stream, count, timeout=5.0):
    lines = []

    def read():
        for _ in range(count):
            lines.append(stream.readline().rstrip("\n"))

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(timeout)
    if reader.is_alive():
        pytest.fail("Timed out waiting for Web startup output.")
    return lines


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("host", "family"),
    [
        pytest.param("127.0.0.1", socket.AF_INET, id="ipv4-loopback"),
        pytest.param("::1", socket.AF_INET6, id="ipv6-loopback"),
    ],
)
def test_web_mode_announces_usable_url_after_startup(host, family):
    port = _free_port(host, family)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "web",
            "--no-open",
            "--host",
            host,
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
        status = _wait_for_status(port, host=host)
        assert status["stale"] is False
        assert sum(item["rows"] for item in status["files"]) > 0
        assert process.stdout is not None
        output = _read_lines(process.stdout, 4)
        expected_url = _web_url(host, port)
        assert output == [
            "PQEnalyzer  Web",
            "Data   5,000 rows / 1 file",
            f"Open   {expected_url}",
            "Stop   Ctrl+C",
        ]
        assert "\033[" not in "\n".join(output)

        emitted_url = output[2].removeprefix("Open   ")
        with _open_url(f"{emitted_url}/api/status", timeout=5) as response:
            assert json.load(response)["stale"] is False
        assert _wait_for_hello(port, host=host)
        with _open_url(f"{emitted_url}/api/events", timeout=5) as stream:
            assert stream.readline().startswith(b"retry:")
            process.send_signal(signal.SIGINT)
            stdout_tail, stderr = process.communicate(timeout=5)
        assert stdout_tail == ""
        assert process.returncode == 130
        assert stderr.count("Server ready.") == 1
        assert stderr.count("Server stopped.") == 1
        assert "Detected PQ energy input" not in stderr
        assert "Uvicorn running" not in stderr
        assert "GET /api/" not in stderr
        assert "Traceback" not in stderr
        assert "CancelledError" not in stderr
        assert "KeyboardInterrupt" not in stderr
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_debug_log_level_enables_http_access_output():
    """Debug mode exposes request diagnostics without changing server behavior."""
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "PQEnalyzer",
            "web",
            "--no-open",
            "--log-level",
            "debug",
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
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)

        assert "PQEnalyzer  Web" in stdout
        assert process.returncode == 130
        diagnostics = stdout + stderr
        assert "GET /api/status" in diagnostics
        assert "200 OK" in diagnostics
        assert "Detected PQ energy input" not in diagnostics
        assert "Traceback" not in diagnostics
        assert "KeyboardInterrupt" not in diagnostics
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_web_analysis_flow_in_browser(tmp_path):
    """Dashboard, analysis modes, keyboard values and stale refresh work together."""
    import shutil

    inputs = []
    for name in ("md-01", "md-02"):
        source = PROJECT_ROOT / "tests" / "data" / f"{name}.en"
        destination = tmp_path / source.name
        shutil.copyfile(source, destination)
        shutil.copyfile(source.with_suffix(".info"),
                        destination.with_suffix(".info"))
        inputs.append(destination)

    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", "web", "--no-open",
         "--port", str(port), *(str(path) for path in inputs)],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_status(port)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"http://127.0.0.1:{port}/")
            page.get_by_role("button", name="TEMPERATURE K", exact=False).click()
            chart = page.get_by_role("group", name="Time series chart.", exact=False)
            chart.focus()
            chart.press("Home")
            expect(chart.locator("[aria-live]")).to_contain_text("All data")
            chart.press("c")
            expect(chart.locator("[aria-live]")).to_contain_text("cum avg")
            chart.press("c")
            expect(chart.locator("[aria-live]")).to_contain_text("All data")

            with page.expect_download() as download_info:
                page.get_by_role("button", name="Download time chart as PNG").click()
            download = download_info.value
            png = tmp_path / download.suggested_filename
            download.save_as(png)
            from PIL import Image
            with Image.open(png) as image:
                assert image.format == "PNG"
                assert image.height > chart.locator("canvas").evaluate(
                    "canvas => canvas.height")

            page.get_by_role("button", name="Analysis 1").click()
            page.get_by_role("button", name="Autocorrelation").click()
            correlation = page.get_by_role("group", name="Autocorrelation by lag.", exact=False)
            correlation.focus()
            correlation.press("Home")
            expect(correlation.locator("[aria-live]")).to_contain_text("Lag (steps) 0")

            page.get_by_role("tab", name="Histogram").click()
            histogram = page.get_by_role("group", name="Histogram,", exact=False)
            histogram.focus()
            histogram.press("End")
            expect(histogram.locator("[aria-live]")).to_contain_text("samples")

            page.set_viewport_size({"width": 844, "height": 390})
            chart_bounds = histogram.bounding_box()
            assert chart_bounds is not None
            assert chart_bounds["y"] + chart_bounds["height"] <= 390
            page.set_viewport_size({"width": 1280, "height": 800})

            page.get_by_role("button", name="Options", exact=True).click()
            page.get_by_role("tab", name="Series").click()
            page.get_by_role("button", name="Analysis 1").click()
            page.get_by_role("button", name="Clear analysis").click()
            page.set_viewport_size({"width": 600, "height": 800})
            page.get_by_role("tab", name="Histogram").click(timeout=2000)
            page.get_by_role("group", name="Histogram,", exact=False).wait_for()
            page.get_by_role("dialog", name="Histogram options").wait_for(state="hidden")
            page.set_viewport_size({"width": 1280, "height": 800})

            page.get_by_role("button", name="Pause auto-refresh").click()
            stat = inputs[0].stat()
            os.utime(inputs[0], ns=(stat.st_mtime_ns + 2_000_000_000,) * 2)
            page.get_by_role("button", name="Resume auto-refresh").locator(
                ".pq-tag-value").get_by_text("stale").wait_for(timeout=10000)
            page.get_by_role("button", name="Resume auto-refresh").click()
            page.get_by_role("button", name="Pause auto-refresh").locator(
                ".pq-tag-value").get_by_text("watching").wait_for(timeout=10000)
            browser.close()
        process.send_signal(signal.SIGINT)
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 130
        assert stderr.count("Input data changed on disk.") == 1
        assert stderr.count("Refreshed 10 rows / 2 files.") == 1
        assert stderr.count("Server stopped.") == 1
        assert "GET /api/" not in stderr
        assert "Traceback" not in stderr
    finally:
        _terminate_process(process)


@pytest.mark.e2e
def test_histogram_loads_without_series_endpoint():
    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "PQEnalyzer", "web", "--no-open",
         "--port", str(port), str(EXAMPLE_FILE)],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_status(port)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.route(
                "**/api/series?*",
                lambda route: route.fulfill(
                    status=503,
                    content_type="application/json",
                    body='{"detail":"Series unavailable"}',
                ),
            )
            page.goto(f"http://127.0.0.1:{port}/#p=TEMPERATURE&m=histogram")
            histogram = page.get_by_role(
                "group", name=re.compile(r"Histogram, .* samples"),
            )
            histogram.wait_for(timeout=10000)
            assert histogram.is_visible()
            browser.close()
    finally:
        _terminate_process(process)
