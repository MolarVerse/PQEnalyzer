from types import SimpleNamespace

from PQEnalyzer.apps import file_watcher
from PQEnalyzer.apps.file_watcher import FileChangeWatcher


def test_file_change_watcher_notifies_for_loaded_file(tmp_path):
    energy_file = tmp_path / "run.en"
    calls = []
    watcher = FileChangeWatcher([energy_file], lambda: calls.append("run"))
    event = SimpleNamespace(
        event_type="modified",
        is_directory=False,
        src_path=str(energy_file),
    )

    watcher.notify(event)

    assert calls == ["run"]


def test_file_change_watcher_notifies_for_moved_destination(tmp_path):
    energy_file = tmp_path / "run.en"
    replacement = tmp_path / ".run.en.tmp"
    calls = []
    watcher = FileChangeWatcher([energy_file], lambda: calls.append("run"))
    event = SimpleNamespace(
        event_type="moved",
        is_directory=False,
        src_path=str(replacement),
        dest_path=str(energy_file),
    )

    watcher.notify(event)

    assert calls == ["run"]


def test_file_change_watcher_ignores_directories_and_unloaded_files(tmp_path):
    energy_file = tmp_path / "run.en"
    other_file = tmp_path / "other.en"
    calls = []
    watcher = FileChangeWatcher([energy_file], lambda: calls.append("run"))

    watcher.notify(
        SimpleNamespace(is_directory=True, src_path=str(energy_file)))
    watcher.notify(
        SimpleNamespace(is_directory=False, src_path=str(other_file)))

    assert calls == []


def test_file_change_watcher_schedules_unique_parent_directories(
        tmp_path, monkeypatch):
    first = tmp_path / "a" / "first.en"
    second = tmp_path / "a" / "second.en"
    third = tmp_path / "b" / "third.en"
    scheduled = []

    class FakeObserver:

        def schedule(self, handler, directory, recursive):
            scheduled.append((handler, directory, recursive))

        def start(self):
            scheduled.append(("start", None, None))

        def stop(self):
            scheduled.append(("stop", None, None))

        def join(self, timeout=None):
            scheduled.append(("join", timeout, None))

    monkeypatch.setattr(file_watcher, "Observer", FakeObserver)

    watcher = FileChangeWatcher([first, second, third], lambda: None)

    assert watcher.start() is True
    watcher.stop()

    assert [entry[1] for entry in scheduled[:2]] == [
        str(tmp_path / "a"),
        str(tmp_path / "b"),
    ]
    assert scheduled[0][2] is False
    assert scheduled[1][2] is False
    assert scheduled[2] == ("start", None, None)
    assert scheduled[-2:] == [("stop", None, None), ("join", 1.0, None)]


def test_file_change_watcher_reports_unavailable_observer(monkeypatch):
    monkeypatch.setattr(file_watcher, "Observer", None)

    watcher = FileChangeWatcher(["run.en"], lambda: None)

    assert watcher.start() is False
