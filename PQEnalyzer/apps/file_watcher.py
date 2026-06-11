"""
File-change watcher used by the GUI auto-refresh flow.
"""

from pathlib import Path

from .._logging import get_logger

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover - dependency is installed at runtime
    FileSystemEventHandler = object
    Observer = None


logger = get_logger(__name__)


class _InputFileEventHandler(FileSystemEventHandler):
    """
    Forward watchdog events for files currently loaded in the app.
    """

    def __init__(self, watcher):
        self.watcher = watcher

    def on_any_event(self, event):
        """
        Handle writes, atomically replaced files, and close-write events.
        """

        if event.event_type not in {"modified", "created", "moved", "closed"}:
            return

        self.watcher.notify(event)


class FileChangeWatcher:
    """
    Watch loaded input files and call a callback when one changes.
    """

    def __init__(self, filenames, callback):
        self.filenames = {Path(filename).resolve() for filename in filenames}
        self.callback = callback
        self.observer = None

    def start(self) -> bool:
        """
        Start watching parent folders of the configured files.
        """

        if Observer is None:
            logger.warning("Auto-refresh unavailable: watchdog is not installed.")
            return False

        self.observer = Observer()
        handler = _InputFileEventHandler(self)
        for directory in sorted({filename.parent for filename in self.filenames}):
            self.observer.schedule(handler, str(directory), recursive=False)

        self.observer.start()
        return True

    def stop(self) -> None:
        """
        Stop the background observer if it is running.
        """

        if self.observer is None:
            return

        self.observer.stop()
        self.observer.join(timeout=1.0)
        self.observer = None

    def notify(self, event) -> None:
        """
        Run the callback when a watchdog event belongs to a loaded file.
        """

        if self.__matches_loaded_file(event):
            self.callback()

    def __matches_loaded_file(self, event) -> bool:
        """
        Return whether an event path is one of the loaded files.
        """

        if getattr(event, "is_directory", False):
            return False

        paths = [getattr(event, "src_path", None)]
        destination = getattr(event, "dest_path", None)
        if destination:
            paths.append(destination)

        for path in paths:
            if path is None:
                continue
            if Path(path).resolve() in self.filenames:
                return True

        return False
