import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


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
            assert "All data" in chart.locator("[aria-live]").inner_text()

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
            assert "Lag (steps) 0" in correlation.locator("[aria-live]").inner_text()

            page.get_by_role("tab", name="Histogram").click()
            histogram = page.get_by_role("group", name="Histogram,", exact=False)
            histogram.focus()
            histogram.press("End")
            assert "samples" in histogram.locator("[aria-live]").inner_text()

            page.set_viewport_size({"width": 844, "height": 390})
            chart_bounds = histogram.bounding_box()
            assert chart_bounds is not None
            assert chart_bounds["y"] + chart_bounds["height"] <= 390
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
