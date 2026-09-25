"""
Observable-vs-diagnostic tests for the PQEnalyzer web front end.

Diagnostics (timers, counters, fixed metadata) stay viewable but must
never imply convergence: they carry a ``kind`` marker and no computed
``analysis`` verdict.
"""

from pathlib import Path

import pytest

from PQEnalyzer.energy_access import parameter_kind

pytest.importorskip("fastapi", reason="web preview dependency not installed")

from PQEnalyzer.web.app import create_app  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
MD_01 = str(DATA / "md-01.en")
MD_02 = str(DATA / "md-02.en")


@pytest.fixture(name="client")
def client_fixture():
    from fastapi.testclient import TestClient

    application = create_app([MD_01, MD_02], "auto")
    with TestClient(application) as client:
        yield client


def test_parameter_kind_names():
    assert parameter_kind("LOOPTIME") == "diagnostic"
    assert parameter_kind("N(QM-ATOMS)") == "diagnostic"
    assert parameter_kind("N(SM-MOL)") == "diagnostic"
    assert parameter_kind("TEMPERATURE") == "observable"
    assert parameter_kind("SOME-NEW-PHYSICAL-THING") == "observable"


def test_parameter_kind_zero_variance():
    assert parameter_kind("CUSTOM-COUNTER", [7.0, 7.0, 7.0]) == "diagnostic"
    assert parameter_kind("CUSTOM-COUNTER", [7.0, 7.0, 7.0000001]) == "observable"
    assert parameter_kind("CUSTOM-COUNTER", []) == "observable"
    assert parameter_kind("CUSTOM-COUNTER", [None, float("nan")]) == "observable"
    assert parameter_kind("CUSTOM-COUNTER", None) == "observable"


def test_parameters_carry_kind(client):
    kinds = {
        item["name"]: item["kind"]
        for item in client.get("/api/parameters").json()["parameters"]
    }
    assert kinds["LOOPTIME"] == "diagnostic"
    assert kinds["N(QM-ATOMS)"] == "diagnostic"
    assert kinds["TEMPERATURE"] == "observable"


def test_summaries_carry_kind(client):
    kinds = {
        item["name"]: item["kind"]
        for item in client.get("/api/summaries").json()["summaries"]
    }
    assert kinds["LOOPTIME"] == "diagnostic"
    assert kinds["TEMPERATURE"] == "observable"


def test_observable_summary_has_analysis(client):
    body = client.get("/api/summary", params={"parameter": "TEMPERATURE"}).json()
    assert body["kind"] == "observable"
    assert "analysis" in body["combined"]


def test_diagnostic_summary_has_no_analysis(client):
    body = client.get("/api/summary", params={"parameter": "LOOPTIME"}).json()
    assert body["kind"] == "diagnostic"
    assert "analysis" not in body["combined"]
    # Stats themselves still work: diagnostics stay viewable.
    assert body["combined"]["rows"] > 0
