import time
import os
from typing import Protocol

from watchdog.observers import Observer as WatchdogObserver
from watchdog.events import FileSystemEventHandler

from pythonbin.transcript.parser import Transcript, TranscriptParser
from .config import Config


class Observer(Protocol):
    def update(self, payload: Transcript):
        ...


class PrintObserver(Observer):
    def update(self, payload: Transcript):
        print(payload)


class TranscriptFileWatcher:
    def __init__(
        self,
        filepath: str,
        config: Config,
        observer: Observer,
        transcript_parser: TranscriptParser | None = None,
    ):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist.")
        if not os.path.isfile(filepath):
            raise ValueError(f"Path {filepath} is not a file.")

        self.filepath = filepath
        self.config = config
        self.watchdog_observer = observer
        self.last_modified = os.path.getmtime(filepath)
        self.running = True
        self.observer = observer

        if transcript_parser is None:
            self.transcript_parser = TranscriptParser(filepath)
        else:
            self.transcript_parser = transcript_parser

        self.setup_watcher()

    def setup_watcher(self):
        """Set up file system watcher with fallback to polling."""
        if self.can_use_watchdog():
            self.setup_watchdog()
        else:
            self.setup_polling()

    def can_use_watchdog(self):
        # Placeholder for determining if watchdog can be used
        return True

    def setup_watchdog(self):
        """Set up watchdog observer."""
        event_handler = FileChangeHandler(self.handle_file_change)
        self.watchdog_observer = WatchdogObserver()
        self.watchdog_observer.schedule(
            event_handler, os.path.dirname(self.filepath), recursive=False
        )
        self.watchdog_observer.start()

    def setup_polling(self):
        """Fallback to polling if watchdog is not available."""
        while self.running:
            self.poll_for_changes()
            time.sleep(self.config.polling_interval)

    def poll_for_changes(self):
        """Check file for changes by last modified time."""
        current_modified = os.path.getmtime(self.filepath)
        if current_modified != self.last_modified:
            self.last_modified = current_modified
            self.handle_file_change()

    def handle_file_change(self):
        """Handle the file change event."""
        print(f"File {self.filepath} has changed.")
        transcript = Transcript(list(self.transcript_parser.parse()))
        self.observer.update(transcript)

    def stop(self):
        """Stop the watcher."""
        if self.watchdog_observer:
            self.watchdog_observer.stop()
            self.watchdog_observer.join()
        self.running = False


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, change_callback):
        self.change_callback = change_callback

    def on_any_event(self, event):
        print(f"Event: {event}")
        if event.is_directory:
            return
        if event.src_path.endswith(".txt"):
            self.change_callback()


def get_newest_file(directory, file_extension=".txt"):
    """Get the newest file in a directory with a specific extension."""
    directory = os.path.expanduser(directory)
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(file_extension) and os.path.isfile(os.path.join(directory, f))
    ]
    if not files:
        print("No files found in the directory.")
        return None
    return max(files, key=os.path.getmtime)


def run_main():
    default_dir = "~/Music/Audio Hijack/Transcript"
    newest_file = get_newest_file(default_dir)

    if newest_file is None:
        print("No transcript file available to monitor.")
        return

    observer = PrintObserver()
    config = Config()
    watcher = TranscriptFileWatcher(newest_file, config, observer)
    time.sleep(20)
    watcher.stop()


if __name__ == "__main__":
    run_main()
