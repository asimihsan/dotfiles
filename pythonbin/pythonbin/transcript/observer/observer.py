from typing import Protocol

from pythonbin.transcript.model import Transcript


class Observer(Protocol):
    def update(self, payload: Transcript):
        ...
