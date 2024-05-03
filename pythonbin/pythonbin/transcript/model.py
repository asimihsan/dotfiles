import datetime

from pydantic import BaseModel, computed_field


class Transcript(BaseModel):
    entries: list["TranscriptEntry"]

    @computed_field
    def elapsed_time_in_minutes(self) -> str:
        if len(self.entries) == 0:
            return "0 minutes"

        seconds = self.entries[-1].time.total_seconds()
        minutes = seconds // 60
        return f"{minutes} minutes"


class TranscriptEntry(BaseModel):
    time: datetime.timedelta
    speaker: str
    text: str
