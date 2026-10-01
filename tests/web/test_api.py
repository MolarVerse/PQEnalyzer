"""
API tests for the PQEnalyzer web front end.

The web layer must stay a thin shaping pass over the shared readers and
plot math: every endpoint is exercised here so refactors cannot silently
break the JSON contract the React app consumes.
"""

from pathlib import Path

import numpy as np
import pytest

DATA = Path(__file__).resolve().parents[1] / "data"
MD_01 = str(DATA / "md-01.en")
MD_02 = str(DATA / "md-02.en")

pytest.importorskip("fastapi", reason="web dependency not installed")

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


def test_series_combines_files_in_input_order(client):
    """
    Short series arrive whole; transport metadata stays consistent.
    """
    body = client.get(
        "/api/series", params={"parameter": "TEMPERATURE"}).json()
    assert body["unit"] == "K"
    assert body["time_unit"] == "ps"
    assert body["time_label"] == "Simulation Time"
    assert body["source_count"] == 2
    assert len(body["series"]) == 1
    combined = body["series"][0]
    assert combined["label"] == "All data"
    assert combined["rows"] == 10
    assert "stride" not in combined
    assert combined["downsampled"] is False
    assert combined["time"] == list(range(1, 11))
    assert len(combined["values"]) == 10
    assert combined["min"] <= combined["max"]


def test_series_sampling_honours_max_points(client):
    """
    Tight budgets retain the endpoints and report that points were omitted.
    """
    body = client.get("/api/series", params={
        "parameter": "TEMPERATURE", "max_points": "2"}).json()
    combined = body["series"][0]
    assert combined["rows"] == 10
    assert "stride" not in combined
    assert combined["downsampled"] is True
    assert len(combined["values"]) == 2
    assert combined["time"] == [1.0, 10.0]


def test_downsampling_retains_spike_and_gap():
    """A narrow event and a missing interval remain visible on long charts."""
    from PQEnalyzer.web.api import _downsample

    time = np.arange(10001, dtype=float)
    values = np.zeros(time.size)
    values[1] = 100.0
    values[4001] = np.nan

    sampled_time, sampled_values = _downsample(time, values, 4000)

    assert sampled_time.size <= 4000
    assert sampled_time[0] == 0
    assert sampled_time[-1] == 10000
    assert 100.0 in sampled_values
    assert np.isnan(sampled_values).any()


def test_unknown_parameter_is_404(client):
    """
    Unknown parameters fail loudly instead of returning empty charts.
    """
    response = client.get("/api/series", params={"parameter": "NOPE"})
    assert response.status_code == 404


def test_unknown_parameter_fails_each_analysis_endpoint(client):
    """The UI receives an explicit error instead of an empty scientific plot."""
    for endpoint, status in (
        ("/api/overlays", 422),
        ("/api/histogram", 422),
        ("/api/summary", 404),
    ):
        response = client.get(endpoint, params={"parameter": "NOPE"})
        assert response.status_code == status
        assert "NOPE" in response.json()["detail"]


def test_refresh_failure_is_reported_without_cached_success(client, monkeypatch):
    """A failed reread is visible to the user rather than silently accepted."""
    from PQEnalyzer.web.api import WebState

    def fail_refresh(_state):
        raise OSError("source disappeared")

    monkeypatch.setattr(WebState, "refresh", fail_refresh)
    response = client.post("/api/refresh")
    assert response.status_code == 500
    assert "source disappeared" in response.json()["detail"]


def test_missing_web_bundle_has_a_clear_error(monkeypatch, tmp_path):
    """An editable install without built assets explains how to build them."""
    from fastapi.testclient import TestClient
    from PQEnalyzer.web import app as web_app

    monkeypatch.setattr(web_app, "STATIC_DIR", tmp_path / "missing")
    with TestClient(web_app.create_app([MD_01], "auto")) as test_client:
        response = test_client.get("/")
    assert response.status_code == 404
    assert "frontend not built" in response.json()["detail"]


def test_overlays_use_shared_feature_math(client):
    """
    References and moving windows use the same combined sequence.
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
    assert all("source_index" not in item for item in body["overlays"])
    assert all(item["axis"] == "time" for item in body["overlays"])
    assert body["overlays"][0]["time"] == [1.0, 10.0]
    running = body["overlays"][1]
    assert running["time"] == list(range(2, 10))
    values = client.get("/api/series", params={
        "parameter": "TEMPERATURE"}).json()["series"][0]["values"]
    assert running["values"][0] == pytest.approx(sum(values[:3]) / 3)
    # The window centered at the file boundary includes both files.
    assert running["values"][4] == pytest.approx(sum(values[4:7]) / 3)


def test_all_web_overlays_have_distinct_scopes_and_axes(client):
    """Every enabled overlay has a useful plotted result on two files."""
    body = client.get("/api/overlays", params={
        "parameter": "PRESSURE",
        "mean": "true",
        "median": "true",
        "cumulative_average": "true",
        "autocorrelation": "true",
        "running_average": "true",
    }).json()
    items = body["overlays"]
    assert [item["key"] for item in items] == [
        "mean", "median", "cumulative_average", "running_average",
        "autocorrelation",
    ]
    assert all(len(item["time"]) >= 2 for item in items)
    assert all(item["axis"] == ("lag" if item["key"] ==
               "autocorrelation" else "time") for item in items)
    assert [item["values"][0] for item in items if item["axis"] == "lag"] == [1.0]
    assert [item["time"] for item in items if item["axis"] == "lag"] == [
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]]
    legacy = client.get("/api/overlays", params={
        "parameter": "PRESSURE", "cummulative_average": "true",
    }).json()["overlays"]
    assert [item["key"] for item in legacy] == ["cumulative_average"]
    assert legacy[0]["values"] == items[2]["values"]


def test_autocorrelation_uses_all_files_as_one_sequence(client):
    """The lag curve includes pairs that cross the file boundary."""
    plotted = client.get("/api/overlays", params={
        "parameter": "PRESSURE", "autocorrelation": "true",
    }).json()["overlays"]
    assert len(plotted) == 1
    assert "source_index" not in plotted[0]

    runs = client.get("/api/series", params={
        "parameter": "PRESSURE",
    }).json()["series"]
    values = np.asarray(runs[0]["values"])
    centered = values - values.mean()
    full_correlation = np.correlate(centered, centered, mode="full")
    expected = full_correlation[len(values) - 1:len(values) + 5]
    expected /= expected[0]
    assert plotted[0]["time"] == list(range(6))
    assert plotted[0]["values"] == pytest.approx(expected)


def test_sparse_parameter_still_uses_one_dataset(client):
    """A parameter in only the second file still uses the combined contract."""
    series_body = client.get("/api/series", params={
        "parameter": "VOLUME"}).json()
    assert series_body["source_count"] == 1
    assert [item["label"] for item in series_body["series"]] == ["All data"]
    overlays = client.get("/api/overlays", params={
        "parameter": "VOLUME", "running_average": "true",
        "autocorrelation": "true",
    }).json()["overlays"]
    assert all("source_index" not in item for item in overlays)


def test_restarted_time_uses_sample_axis_for_every_curve(tmp_path):
    """A repeated time grid retains every observation and aligns analysis."""
    import shutil
    from fastapi.testclient import TestClient

    duplicate = tmp_path / "same-steps.en"
    shutil.copyfile(MD_02, duplicate)
    shutil.copyfile(str(Path(MD_02).with_suffix(".info")),
                    str(duplicate.with_suffix(".info")))
    with TestClient(create_app([MD_02, str(duplicate)], "auto")) as overlap:
        series_body = overlap.get("/api/series", params={
            "parameter": "TEMPERATURE"}).json()
        assert series_body["time_label"] == "Sample"
        assert series_body["time_unit"] == ""
        combined = series_body["series"][0]
        assert combined["time"] == list(range(1, 11))
        assert combined["values"][:5] == combined["values"][5:]
        curves = overlap.get("/api/overlays", params={
            "parameter": "TEMPERATURE", "mean": "true",
            "cumulative_average": "true", "running_average": "true",
            "window_size": "3"}).json()["overlays"]
        assert curves[0]["time"] == [1.0, 10.0]
        assert curves[1]["time"] == list(range(1, 11))
        assert curves[2]["time"] == list(range(2, 10))
        assert curves[2]["values"][4] == pytest.approx(
            sum(combined["values"][4:7]) / 3)
        analysis = overlap.get("/api/summary", params={
            "parameter": "TEMPERATURE"}).json()["combined"]["analysis"]
        assert analysis["equil_time"] is None or 1 <= analysis["equil_time"] <= 10
        histogram = overlap.get("/api/histogram", params={
            "parameter": "TEMPERATURE"}).json()
        assert sum(histogram["series"][0]["counts"]) == 10


def test_histogram_bins_one_combined_distribution(client):
    """
    Histogram counts share edges with mean/median guides.
    """
    body = client.get("/api/histogram", params={
        "parameter": "TEMPERATURE", "bins": "24"}).json()
    assert len(body["edges"]) == 25
    assert [item["rows"] for item in body["series"]] == [10]
    assert body["series"][0]["label"] == "All data"
    assert sum(body["series"][0]["counts"]) == 10
    assert len(body["kde"]) == 1
    assert body["kde"][0]["label"] == "All data"
    assert [guide["label"] for guide in body["guides"]] == [
        "Mean", "Median"]


def test_histogram_defaults_to_bounded_auto_bins(client):
    """The default resolves from all values and avoids empty tiny-sample bins."""
    from PQEnalyzer.web.api import _automatic_bin_count

    values = np.asarray(client.get("/api/series", params={
        "parameter": "TEMPERATURE"}).json()["series"][0]["values"])
    body = client.get("/api/histogram", params={
        "parameter": "TEMPERATURE"}).json()
    assert len(body["edges"]) - 1 == len(
        np.histogram_bin_edges(values, bins="auto")) - 1
    assert sum(body["series"][0]["counts"]) == values.size
    assert _automatic_bin_count(np.r_[np.linspace(0, 1, 1000), 1e12]) == 200
    assert len(client.get("/api/histogram", params={
        "parameter": "TEMPERATURE", "bins": "2"}).json()["edges"]) == 3
    assert client.get("/api/histogram", params={
        "parameter": "TEMPERATURE", "bins": "invalid"}).status_code == 422


def test_summary_reports_combined_stats(client):
    """
    Summary carries combined statistics for the stat strip.
    """
    body = client.get(
        "/api/summary", params={"parameter": "TEMPERATURE"}).json()
    assert "files" not in body
    assert body["combined"]["rows"] == 10
    assert body["combined"]["min"] <= body["combined"]["max"]
    assert isinstance(body["combined"]["drift"], float)
    analysis = body["combined"]["analysis"]
    assert "equilibrated" not in analysis
    assert analysis["discarded_fraction"] == 0.0
    assert 0 < analysis["n_effective"] <= 10
    assert analysis["sem"] is not None


def test_mser_cut_is_not_a_convergence_verdict():
    """A clear step can yield a 50% cut while the full mean remains biased."""
    from PQEnalyzer.web.api import _analysis_of, _stats_of_array

    values = np.r_[np.zeros(50), np.full(50, 10.0)]
    analysis = _analysis_of(values, np.arange(values.size))
    stats = _stats_of_array(values, label="combined", rows=values.size)

    assert analysis["equil_index"] == 50
    assert analysis["discarded_fraction"] == 0.5
    assert "equilibrated" not in analysis
    assert stats["mean"] == 5.0


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
    assert "equilibrated" not in temperature["combined"]["analysis"]


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
