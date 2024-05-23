from dataclasses import dataclass, field
from typing import List


@dataclass
class Page:
    number: int
    content: str


@dataclass
class Chapter:
    title: str
    raw_content: str
    sentences: List[str] = field(default_factory=list)


@dataclass
class Ebook:
    title: str
    chapters: List[Chapter] = field(default_factory=list)


@dataclass
class TocItem:
    href: str
    title: str

    @property
    def filename(self) -> str:
        return self.href.split("#")[0]
