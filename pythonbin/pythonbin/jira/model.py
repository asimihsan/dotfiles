import datetime
from dataclasses import dataclass, field

@dataclass
class Mention:
    id: str
    text: str


@dataclass
class Comment:
    author: str | None
    body: str | None
    updated: datetime.datetime | None = None


@dataclass
class Issue:
    key: str
    summary: str
    description: str | None = None
    issue_type: str | None = None
    comments: list[Comment] = field(default_factory=list)


@dataclass
class Epic:
    key: str
    summary: str
    description: str | None = None
    program_manager: str | None = None
    launch_date: datetime.datetime | None = None
    target_release_date: datetime.datetime | None = None
    child_issues: list[Issue] = field(default_factory=list)
