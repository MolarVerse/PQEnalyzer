"""
API tests for the PQEnalyzer web front end (LOCAL-ONLY preview).

The web layer must stay a thin shaping pass over the shared readers and
plot math: every endpoint is exercised here so refactors cannot silently
break the JSON contract the React app consumes.
"""

from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"
MD_01 = str(DATA / "md-01.en")
MD_02 = str(DATA / "md-02.en")

pytest.importorskip("fastapi", reason="web preview dependency not installed")

from PQEnalyzer.web.app import create_app  # noqa: E402


@pytest.fixture(name="client")
def client_fixture():
    """
    Return a test client serving two energy files.
    """
    from fastapi.testclient import TestClient

    application = create_app([MD_01, MD_02], "auto")
    with TestClient(application) as client:
        yield client


def test_meta_lists_files_and_axis(client):
    """
    Meta reports the reader kind, time axis, and per-file rows.
    """
    body = client.get("/api/meta").json()
    assert body["reader"] == "Reader"
    assert body["time_label"] == "Simulation Time"
    assert [item["rows"] for item in body["files"]] == [5, 5]
    assert body["stale"] is False


def test_parameters_expose_units_and_coverage(client):
    """
    Parameters carry units plus file coverage for the sidebar list.
    """
    parameters = {
        item["name"]: item
        for item in client.get("/api/parameters").json()["parameters"]
    }
    assert parameters["TEMPERATURE"]["unit"] == "K"
    assert parameters["TEMPERATURE"]["files"] == 2
    assert parameters["TEMPERATURE"]["rows"] == 10


def test_series_downsamples_large_files(client):
    """
    Short series arrive whole; transport metadata stays consistent.
    """
    body = client.get(
        "/api/series", params={"parameter": "TEMPERATURE"}).json()
    assert body["unit"] == "K"
    assert body["time_unit"] == "ps"
    assert len(body["series"]) == 2
    first = body["series"][0]
    assert first["rows"] == 5
    assert first["stride"] == 1
    assert first["downsampled"] is False
    assert len(first["values"]) == 5
    assert first["min"] <= first["max"]


def test_series_stride_honours_max_points(client):
    """
    Tight budgets stride the series and say so in the payload.
    """
    body = client.get("/api/series", params={
        "parameter": "TEMPERATURE", "max_points": "2"}).json()
    first = body["series"][0]
    assert first["rows"] == 5
    assert first["stride"] == 3
    assert first["downsampled"] is True
    assert len(first["values"]) == 2


def test_unknown_parameter_is_404(client):
    """
    Unknown parameters fail loudly instead of returning empty charts.
    """
    response = client.get("/api/series", params={"parameter": "NOPE"})
    assert response.status_code == 404


def test_overlays_use_shared_feature_math(client):
    """
    Overlay labels match the desktop feature registry exactly.
    """
    body = client.get("/api/overlays", params={
        "parameter": "TEMPERATURE",
        "mean": "true",
        "running_average": "true",
        "window_size": "3",
    }).json()
    assert [item["label"] for item in body["overlays"]] == [
        "Mean", "Running Average (3)"]
    assert all(len(item["values"]) > 0 for item in body["overlays"])


def test_difference_without_shared_steps_is_422(client):
    """
    Difference validation from the shared math surfaces as HTTP 422.
    """
    response = client.get("/api/overlays", params={
        "parameter": "TEMPERATURE",
        "difference": "true",
    })
    assert response.status_code == 422
    assert "shared" in response.json()["detail"]


def test_histogram_bins_on_shared_edges(client):
    """
    Histogram counts share edges with mean/median guides.
    """
    body = client.get("/api/histogram", params={
        "parameter": "TEMPERATURE", "bins": "24"}).json()
    assert len(body["edges"]) == 25
    assert [item["rows"] for item in body["series"]] == [5, 5]
    # Five-row fixtures are below the KDE minimum: no curves, no crash.
    assert body["kde"] == []
    assert [guide["label"] for guide in body["guides"]] == [
        "Mean", "Median"]


def test_summary_reports_combined_stats(client):
    """
    Summary carries per-file plus combined statistics for the stat strip.
    """
    body = client.get(
        "/api/summary", params={"parameter": "TEMPERATURE"}).json()
    assert len(body["files"]) == 2
    assert body["combined"]["rows"] == 10
    assert body["combined"]["min"] <= body["combined"]["max"]
    assert isinstance(body["combined"]["drift"], float)
    analysis = body["combined"]["analysis"]
    assert analysis["equilibrated"] is True
    assert analysis["discarded_fraction"] == 0.0
    assert 0 < analysis["n_effective"] <= 10
    assert analysis["sem"] is not None


def test_summaries_cover_every_parameter(client):
    """
    The dashboard payload includes sparkline values for each parameter.
    """
    body = client.get("/api/summaries").json()
    assert len(body["summaries"]) >= 9
    temperature = next(
        item for item in body["summaries"] if item["name"] == "TEMPERATURE")
    assert 0 < len(temperature["spark"]) <= 120
    assert len(temperature["hist"]["edges"]) == 25
    assert len(temperature["hist"]["counts"]) == 24
    assert sum(temperature["hist"]["counts"]) == 10
    assert temperature["combined"]["analysis"]["equilibrated"] is True


def test_kde_of_returns_count_scaled_curves():
    """
    KDE curves sample a grid and scale to bin counts; degenerate input
    returns None instead of crashing the histogram endpoint.
    """
    import numpy as np

    from PQEnalyzer.web.api import _kde_of

    rng = np.random.default_rng(3)
    values = rng.normal(0.0, 1.0, size=500)
    edges = np.histogram_bin_edges(values, bins=24)
    curve = _kde_of(values, edges)
    assert curve is not None
    assert len(curve["x"]) == 200
    assert max(curve["y"]) > 0

    assert _kde_of(np.full(50, 1.0), edges) is None
    assert _kde_of(np.array([1.0, 2.0]), edges) is None


def test_status_and_refresh_roundtrip(client):
    """
    Status reports staleness; refresh re-reads and clears it.
    """
    assert client.get("/api/status").json()["stale"] is False
    assert client.post("/api/refresh").json()["stale"] is False


def test_export_csv_is_long_form_with_header(client):
    """
    CSV export documents parameter/unit/times in comments, one row per step.
    """
    text = client.get(
        "/api/export.csv", params={"parameter": "TEMPERATURE"}).text
    lines = text.splitlines()
    assert lines[0] == "# parameter: TEMPERATURE"
    assert lines[1] == "# unit: K"
    assert lines[3] == "file,time,value"
    assert len(lines) == 4 + 10
