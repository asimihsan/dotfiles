import re
import datetime
from typing import Generator

from pythonbin.transcript.model import TranscriptEntry

timestamp_pattern = r"^\[(\d{2}:\d{2}:\d{2}\.\d{2})]"
speaker_pattern = r"(.*?):"
text_pattern = r"(.*)$"
pattern = re.compile(rf"{timestamp_pattern}\s+?{speaker_pattern}\s+{text_pattern}")


def parse_line(line: str) -> TranscriptEntry | None:
    """Parse a single line of the transcript.

    Format is lines like:

    [00:00:00.22] Me:	Hey there!

    [00:00:01.64] Other(s): Hi!

    >>> parse_line("[00:00:00.22] Me:	Hey there!")
    TranscriptEntry(time=datetime.timedelta(microseconds=22000), speaker='Me', text='Hey there!')
    """

    match = pattern.match(line)
    if not match:
        return None

    timestamp, speaker, text = match.groups()
    time = datetime.timedelta(
        hours=int(timestamp[:2]),
        minutes=int(timestamp[3:5]),
        seconds=float(timestamp[6:8]),
        microseconds=int(timestamp[9:]) * 1000,
    )
    return TranscriptEntry(time=time, speaker=speaker, text=text)


class TranscriptParser:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse(self) -> Generator[TranscriptEntry, None, None]:
        """Parse the transcript file and yield TranscriptEntry objects."""
        with open(self.filepath, "r") as file:
            for line in file:
                entry = parse_line(line)
                if entry:
                    yield entry
