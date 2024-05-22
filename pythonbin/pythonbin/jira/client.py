from typing import Optional, Generator

from jira import JIRA, JIRAError

from pythonbin.jira.model import Epic, Issue
from pythonbin.jira.parser import EpicParser, IssueParser


class JiraClient:
    program_manager_field = "customfield_12405"
    launch_date_field = "customfield_12400"
    target_date_field = "customfield_12401"

    def __init__(self, server: str, user_email: str, token_auth: str):
        self.jira = JIRA(
            server=server,
            basic_auth=(user_email, token_auth),
        )
        self.jira._options.update({"rest_api_version": 3})

    def get_epics(self, project_key: str, program_manager: Optional[str] = None) -> Generator[Epic, None, None]:
        jql_parts = [f"project = {project_key}", "issuetype = Epic"]
        if program_manager:
            jql_parts.append(f'"Program Manager" = "{program_manager}"')

        jql = " AND ".join(jql_parts)

        start_at = 0
        max_results = 50
        total = 1  # Initialize to any non-zero value

        while start_at < total:
            issues = self.jira.search_issues(jql, startAt=start_at, maxResults=max_results)
            total = issues.total
            start_at += max_results

            for issue in issues:
                epic_parser = EpicParser(issue)
                epic = epic_parser.parse(
                    program_manager_field=self.program_manager_field,
                    launch_date_field=self.launch_date_field,
                    target_date_field=self.target_date_field,
                )

                for child_issue in self.get_child_issues(epic.key):
                    epic.child_issues.append(child_issue)

                yield epic

    def get_child_issues(self, epic_key: str) -> Generator[Issue, None, None]:
        jql = f"'Epic Link' = {epic_key}"
        start_at = 0
        max_results = 50
        total = 1

        while start_at < total:
            issues = self.jira.search_issues(jql, startAt=start_at, maxResults=max_results, expand="renderedFields")
            total = issues.total
            start_at += max_results

            for issue in issues:
                issue_parser = IssueParser(issue)
                child_issue = issue_parser.parse()
                yield child_issue

    def get_epic_by_key(self, epic_key: str) -> Optional[Epic]:
        try:
            issue = self.jira.issue(epic_key)
            epic_parser = EpicParser(issue)
            epic = epic_parser.parse(
                program_manager_field=self.program_manager_field,
                launch_date_field=self.launch_date_field,
                target_date_field=self.target_date_field,
            )

            for child_issue in self.get_child_issues(epic.key):
                epic.child_issues.append(child_issue)

            return epic
        except Exception as e:
            print(f"Error fetching epic {epic_key}: {e}")
            return None

    def get_issue_by_key(self, issue_key: str) -> Optional[Issue]:
        """
        Fetches a Jira issue by its key.

        :param issue_key: The key of the Jira issue to fetch.
        :return: The Jira issue if found, otherwise None.
        """
        try:
            issue = self.jira.issue(issue_key)
            issue_parser = IssueParser(issue)
            return issue_parser.parse()
        except JIRAError as e:
            if e.status_code == 404:
                print(f"Issue with key {issue_key} not found.")
                return None
            else:
                raise
