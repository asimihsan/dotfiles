import datetime
import re
from typing import Optional

import dateparser
import jira
import markdown

from pythonbin.jira.model import Epic, Issue


class EpicParser:
    def __init__(self, issue: jira.Issue):
        self.issue = issue

    def parse(self, program_manager_field: str, launch_date_field: str, target_date_field: str) -> Epic:
        epic = Epic(
            key=self.issue.key,
            summary=self.issue.fields.summary,
            description=self.parse_description_markdown(),
            program_manager=self.parse_program_manager(program_manager_field=program_manager_field),
            launch_date=self.parse_launch_date(launch_date_field=launch_date_field),
            target_release_date=self.parse_target_date(target_date_field=target_date_field),
        )
        self.parse_summary(epic)
        return epic

    def parse_summary(self, epic: Epic) -> None:
        # Similar to IssueParser.parse_summary(), parse key fields from epic summary
        pass

    def parse_description_markdown(self) -> str:
        if self.issue.fields.description:
            return markdown.markdown(self.issue.fields.description)
        return ""

    def parse_program_manager(self, program_manager_field: str) -> Optional[str]:
        if hasattr(self.issue.fields, program_manager_field):
            user: jira.User = getattr(self.issue.fields, program_manager_field)
            return user.raw["displayName"] if user else None
        return None

    def parse_launch_date(self, launch_date_field: str) -> Optional[datetime.datetime]:
        if hasattr(self.issue.fields, launch_date_field):
            date_str = getattr(self.issue.fields, launch_date_field)
            return dateparser.parse(date_str) if date_str else None
        return None

    def parse_target_date(self, target_date_field: str) -> Optional[datetime.datetime]:
        if hasattr(self.issue.fields, target_date_field):
            date_str = getattr(self.issue.fields, target_date_field)
            return dateparser.parse(date_str) if date_str else None
        return None


class IssueParser:
    def __init__(self, issue: jira.Issue):
        self.issue = issue

    def parse(self) -> Issue:
        issue = Issue(
            key=self.issue.key,
            summary=self.issue.fields.summary,
            description=self.parse_description_markdown(),
            issue_type=self.issue.fields.issuetype.name,
        )
        self.parse_summary(issue)
        return issue

    def parse_summary(self, issue: Issue) -> None:
        # Parse key fields from the summary if present
        # Example format: "Feature: (P0) Resident Automations"
        match = re.match(r"^(\w+):\s*(\(P\d\))?\s*(.+)$", issue.summary)
        if match:
            issue.summary_type = match.group(1)
            issue.priority = match.group(2)
            issue.summary_title = match.group(3)

    def parse_description_markdown(self) -> str:
        if self.issue.fields.description:
            return markdown.markdown(self.issue.fields.description)
        return ""
