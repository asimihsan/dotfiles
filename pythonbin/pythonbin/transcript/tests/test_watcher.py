import datetime
import threading
import time
from typing import Generator

import pytest

from pythonbin.transcript.config import Config
from pythonbin.transcript.transcript import (
    PrintObserver,
    TranscriptFileWatcher,
)
from pythonbin.transcript.observer.observer import Observer
from pythonbin.transcript.model import Transcript


@pytest.fixture
def empty_test_file_for_writing(tmp_path) -> Generator[str, None, None]:
    test_file = tmp_path / "test_file.txt"

    with open(test_file, "w"):
        pass  # noqa

    yield test_file.as_posix()

    test_file.unlink()


class TestObserver(Observer):
    def __init__(self):
        self.seen_payloads = []
        self.payload_event = threading.Event()

    def update(self, payload: Transcript):
        self.seen_payloads.append(payload)
        self.payload_event.set()


def test_observer_receives_updates(empty_test_file_for_writing):
    observer = TestObserver()
    watcher = TranscriptFileWatcher(empty_test_file_for_writing, Config(), observer)

    time.sleep(1)

    # Simulate file change
    with open(empty_test_file_for_writing, "w") as f:
        f.write("[00:02:00.00] Me: Adding a new line for testing.\n\n")

    observer.payload_event.wait(timeout=5)

    assert len(observer.seen_payloads) == 1
    assert len(observer.seen_payloads[0].entries) == 1
    entry = observer.seen_payloads[0].entries[0]
    assert entry.time == datetime.timedelta(seconds=120)
    assert entry.speaker == "Me"
    assert entry.text == "Adding a new line for testing."
