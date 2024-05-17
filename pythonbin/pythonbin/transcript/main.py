import pathlib
import time
import os

from watchdog.observers import Observer as WatchdogObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from pythonbin.transcript.observer.llm_observer import LLMObserver
from pythonbin.transcript.observer.observer import Observer
from pythonbin.transcript.parser import TranscriptParser
from pythonbin.transcript.model import Transcript
from pythonbin.transcript.config import Config


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
        self.last_modified = os.path.getmtime(filepath)
        self.running = True
        self.observer = observer

        if transcript_parser is None:
            self.transcript_parser = TranscriptParser(filepath)
        else:
            self.transcript_parser = transcript_parser

        self.setup_watchdog()

    def setup_watchdog(self):
        """Set up watchdog observer."""
        event_handler = FileChangeHandler(self.handle_file_change, self.filepath)
        self.watchdog_observer = WatchdogObserver()
        self.watchdog_observer.schedule(event_handler, os.path.dirname(self.filepath), recursive=False)
        self.watchdog_observer.start()

        # always trigger once at the beginning
        self.handle_file_change()

    def handle_file_change(self):
        """Handle the file change event."""
        print(f"File {self.filepath} has changed.")
        transcript = Transcript(entries=list(self.transcript_parser.parse()))
        self.observer.update(transcript)

    def stop(self):
        """Stop the watcher."""
        if self.watchdog_observer:
            self.watchdog_observer.stop()
            self.watchdog_observer.join()
        self.running = False


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, change_callback, filepath: str):
        self.change_callback = change_callback
        self.filepath = filepath

    def on_modified(self, event: FileSystemEvent):
        if event.src_path != self.filepath:
            return
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
    # default_dir = "~/Music/Audio Hijack/Transcript"
    # newest_file = get_newest_file(default_dir)

    transcript_file = "/Users/asimi/Downloads/20240418 1602 Transcription.txt"

    prompt_path = pathlib.Path("~/Obsidian/Level/Chats/Prompt.md").expanduser()
    observer = LLMObserver(prompt_path)

    config = Config()
    watcher = TranscriptFileWatcher(transcript_file, config, observer)
    time.sleep(20)
    watcher.stop()


if __name__ == "__main__":
    run_main()
