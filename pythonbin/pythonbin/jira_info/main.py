import argparse
import os

from pythonbin.jira.client import JiraClient


def run_main() -> None:
    parser = argparse.ArgumentParser(description='Fetch Jira epic or issue information.')
    parser.add_argument('--epic_key', type=str, help='Jira epic key to fetch')
    parser.add_argument('--issue_key', type=str, help='Jira issue key to fetch')

    args = parser.parse_args()

    server = os.environ["JIRA_API_SERVER"]
    user_email = os.environ["JIRA_API_EMAIL"]
    token_auth = os.environ["JIRA_API_TOKEN"]
    client = JiraClient(server=server, user_email=user_email, token_auth=token_auth)

    if not args.epic_key and not args.issue_key:
        print("Please provide either --epic_key or --issue_key.")
        return

    if args.epic_key:
        for issue in client.get_child_issues(args.epic_key):
            print(f"{issue.key}: {issue.summary} (type: {issue.issue_type})")
            print("---")
    elif args.issue_key:
        issue = client.get_issue_by_key(args.issue_key)
        if issue:
            print(f"{issue.key}: {issue.summary} (type: {issue.issue_type})")
            print("---")
            print(f"Description: {issue.description}")
            print(f"Comments:")
            for comment in issue.comments:
                print(f"Author: {comment.author}")
                print(f"Updated: {comment.updated}")
                print(f"Body: {comment.body}")
                print("---")
        else:
            print("Issue not found.")


if __name__ == "__main__":
    run_main()
