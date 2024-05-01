import datetime
from dataclasses import dataclass


@dataclass
class Transcript:
    entries: list["TranscriptEntry"]


@dataclass
class TranscriptEntry:
    time: datetime.timedelta
    speaker: str
    text: str
