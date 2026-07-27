import errno
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

    assert watcher.mode is None
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


def test_file_change_watcher_falls_back_after_native_resource_error(
        tmp_path, monkeypatch, caplog):
    energy_file = tmp_path / "run.en"
    calls = []

    class FailingNativeObserver:

        def schedule(self, handler, directory, recursive):
            calls.append(("native-schedule", directory, recursive))

        def start(self):
            raise OSError(errno.EMFILE, "inotify instance limit reached")

        def stop(self):
            calls.append(("native-stop",))

        def join(self, timeout=None):
            calls.append(("native-join", timeout))
            raise RuntimeError("observer thread was not started")

    class FakePollingObserver:

        def schedule(self, handler, directory, recursive):
            calls.append(("polling-schedule", directory, recursive))

        def start(self):
            calls.append(("polling-start",))

        def stop(self):
            calls.append(("polling-stop",))

        def join(self, timeout=None):
            calls.append(("polling-join", timeout))

    monkeypatch.setattr(
        file_watcher,
        "Observer",
        FailingNativeObserver,
    )
    monkeypatch.setattr(
        file_watcher,
        "PollingObserver",
        FakePollingObserver,
    )
    watcher = FileChangeWatcher([energy_file], lambda: None)

    assert watcher.start() is True
    assert watcher.mode == "polling"
    assert ("native-stop",) in calls
    assert ("native-join", 1.0) in calls
    assert ("polling-start",) in calls
    assert "inotify instance limit reached" in caplog.text
    assert "using polling" in caplog.text

    watcher.stop()

    assert watcher.mode is None
    assert calls[-2:] == [
        ("polling-stop",),
        ("polling-join", 1.0),
    ]


def test_file_change_watcher_reports_failed_polling_fallback(
        tmp_path, monkeypatch, caplog):

    class FailingObserver:

        def schedule(self, handler, directory, recursive):
            return None

        def start(self):
            raise OSError(errno.EMFILE, "watch limit reached")

        def stop(self):
            return None

        def join(self, timeout=None):
            return None

    monkeypatch.setattr(file_watcher, "Observer", FailingObserver)
    monkeypatch.setattr(file_watcher, "PollingObserver", FailingObserver)
    watcher = FileChangeWatcher([tmp_path / "run.en"], lambda: None)

    assert watcher.start() is False
    assert watcher.observer is None
    assert watcher.mode is None
    assert "Auto-refresh unavailable" in caplog.text
