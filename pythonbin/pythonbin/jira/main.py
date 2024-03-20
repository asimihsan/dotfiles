import os

from pythonbin.jira.client import JiraClient


def main(server: str,
         user_email: str,
         token_auth: str,
         project_key: str) -> None:
    client = JiraClient(server=server, user_email=user_email, token_auth=token_auth)
    epics = client.get_epics(project_key=project_key)
    for epic in epics:
        print(f"{epic.key}")
        print(epic)
        print("---")


if __name__ == "__main__":
    server = os.environ["JIRA_API_SERVER"]
    user_email = os.environ["JIRA_API_EMAIL"]
    token_auth = os.environ["JIRA_API_TOKEN"]
    project_key = "MDU2"

    main(server=server,
         user_email=user_email,
         token_auth=token_auth,
         project_key=project_key)
