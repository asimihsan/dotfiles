import os

from pythonbin.jira.client import JiraClient


def run_main(epic_key: str) -> None:
    server = os.environ["JIRA_API_SERVER"]
    user_email = os.environ["JIRA_API_EMAIL"]
    token_auth = os.environ["JIRA_API_TOKEN"]
    client = JiraClient(server=server, user_email=user_email, token_auth=token_auth)

    for issue in client.get_child_issues(epic_key):
        print(f"{issue.key}: {issue.summary} (type: {issue.issue_type})")
        # print(f"{issue.description}")
        print("---")
