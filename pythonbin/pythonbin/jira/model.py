import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Issue:
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: Optional[str] = None


@dataclass
class Epic:
    key: str
    summary: str
    description: Optional[str] = None
    program_manager: Optional[str] = None
    launch_date: Optional[datetime.datetime] = None
    target_release_date: Optional[datetime.datetime] = None
    child_issues: List[Issue] = field(default_factory=list)
