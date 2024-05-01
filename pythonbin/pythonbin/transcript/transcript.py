import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import Config


class TranscriptFileWatcher:
    def __init__(self, filepath, config: Config, observer):
        self.filepath = filepath
        self.config = config
        self.observer = observer
        self.last_modified = os.path.getmtime(filepath)
        self.running = True
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
        self.observer = Observer()
        self.observer.schedule(event_handler, self.filepath, recursive=False)
        self.observer.start()

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
        # Here we would parse the file and notify the observer.

    def stop(self):
        """Stop the watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.running = False


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, change_callback):
        self.change_callback = change_callback

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".txt"):
            self.change_callback()


def get_newest_file(directory):
    """Get the newest file in a directory."""
    directory = os.path.expanduser(directory)

    return max(
        (os.path.join(directory, f) for f in os.listdir(directory)),
        key=lambda f: os.path.getmtime(f),
    )


def run_main():
    default_dir = "~/Music/Audio Hijack/Transcript"
    newest_file = get_newest_file(default_dir)

    config = Config()
    watcher = TranscriptFileWatcher(newest_file, config, None)


if __name__ == "__main__":
    run_main()
