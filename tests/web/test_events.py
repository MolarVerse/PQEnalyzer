"""
SSE event tests for the PQEnalyzer web front end (LOCAL-ONLY preview).

The watcher thread plus per-client queues replace the old status poll:
a `hello` carries the current status on connect, one `stale` push fires
per fresh-to-stale transition, and heartbeats bound dead-client linger.
"""

import json
import os
import shutil
import time

import pytest

from PQEnalyzer.web.api import WebState

pytest.importorskip("fastapi", reason="web preview dependency not installed")

DATA = __import__("pathlib").Path(__file__).resolve().parents[1] / "data"
MD_01 = str(DATA / "md-01.en")


@pytest.fixture(name="state")
def state_fixture(tmp_path):
    """
    Return a WebState watching a private copy of an energy file.
    """
    from PQEnalyzer.readers import create_reader

    watched = tmp_path / "watched.en"
    shutil.copyfile(MD_01, watched)
    return WebState(create_reader([str(watched)], "auto")), str(watched)


def _drain_hello(events):
    """
    Consume the retry hint plus hello; return the hello payload.
    """
    assert next(events).startswith("retry: ")
    hello = next(events)
    assert hello.startswith("event: hello\n")
    return json.loads(hello.split("data: ", 1)[1])


def _touch(path):
    """
    Bump mtime by two seconds (well outside timestamp granularity).
    """
    stat = os.stat(path)
    os.utime(path, ns=(stat.st_mtime_ns + 2_000_000_000,) * 2)


def _next_stale(events, timeout=5.0):
    """
    Skip heartbeats until the stale push arrives (watcher scans
    periodically, so the first tick after a touch may be a ping).
    """
    deadline = time.monotonic() + timeout
    while True:
        pushed = next(events)
        if pushed.startswith("event: stale\n"):
            return pushed
        assert time.monotonic() < deadline, f"no stale push in {timeout}s"


def test_hello_carries_current_status(state):
    """
    Connect yields the reconnect hint plus a hello with fresh status.
    """
    web_state, _ = state
    events = web_state.events(heartbeat=60)
    try:
        body = _drain_hello(events)
        assert body["stale"] is False
        assert len(body["files"]) == 1
    finally:
        events.close()
    assert web_state._subscribers == []


def test_stale_push_on_mtime_change(state):
    """
    Touching a watched file pushes exactly one stale event.
    """
    web_state, watched = state
    events = web_state.events(heartbeat=30)
    try:
        _drain_hello(events)
        _touch(watched)
        pushed = _next_stale(events)
        assert json.loads(pushed.split("data: ", 1)[1]) == {"stale": True}
    finally:
        events.close()
    assert web_state._subscribers == []


def test_heartbeat_when_idle(state):
    """
    An idle stream emits ping comments instead of hanging forever.
    """
    web_state, _ = state
    events = web_state.events(heartbeat=0.2)
    try:
        _drain_hello(events)
        assert next(events) == ": ping\n\n"
    finally:
        events.close()


def test_only_one_push_per_transition(state):
    """
    Repeated scans while stale do not spam subscribers.
    """
    web_state, watched = state
    events = web_state.events(heartbeat=0.2)
    try:
        _drain_hello(events)
        _touch(watched)
        pushed = _next_stale(events)
        assert pushed.startswith("event: stale\n")
        # Next ticks are heartbeats, not duplicate stale pushes.
        assert next(events) == ": ping\n\n"
    finally:
        events.close()
