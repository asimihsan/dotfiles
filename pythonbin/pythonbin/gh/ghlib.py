import json
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, List

from pythonbin.command.command import run_command
from pythonbin.gh.models import PullRequestURL


@dataclass
class LinearIssue:
    url: str
    id: str


@dataclass
class Comment:
    author: str
    body: str
    created_at: str

    def __init__(self, payload: dict):
        self.author = payload["user"]["login"]
        self.body = payload["body"]
        self.created_at = payload["created_at"]

    def get_linear_issue(self) -> Optional[LinearIssue]:
        match = re.search(r"https://linear.app/[^/]+/issue/([^/]+)/", self.body)
        if match:
            return LinearIssue(url=match.group(0), id=match.group(1))
        return None


def get_pr_description(pr_url):
    return run_command(f'gh pr view {pr_url} --json "body,comments" -q .body')


def get_pr_diff(pr_url, exclude_files=None):
    if exclude_files is None:
        exclude_files = ["poetry.lock", "pyproject-old.toml"]  # Default files to ignore
    diff_text = run_command(f"gh pr diff {pr_url}")
    filtered_diff = []
    diff_lines = diff_text.split("\n")
    skip = False
    for line in diff_lines:
        if line.startswith("diff --git"):
            skip = any(file_name in line for file_name in exclude_files)
        if not skip:
            filtered_diff.append(line)
    return "\n".join(filtered_diff)


def get_pr_comments(pr_url: PullRequestURL) -> str:
    # Construct the GitHub API endpoint for PR comments
    endpoint = f"/repos/{pr_url.owner}/{pr_url.repo}/pulls/{pr_url.number}/comments"

    # Call the GitHub CLI
    result = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            endpoint,
        ],
        capture_output=True,
        text=True,
    )

    # Check if the call was successful
    if result.returncode != 0:
        print("Error fetching PR comments:", result.stderr)
        return ""

    # Parse the JSON output
    comments = json.loads(result.stdout)

    # Format the comments as Markdown
    markdown_output: list[str] = []
    for comment in comments:
        user_login = comment["user"]["login"]
        diff_hunk = comment["diff_hunk"]
        body = comment["body"]

        # Truncate the diff_hunk if it's too long
        diff_hunk_lines = diff_hunk.split("\n")
        if len(diff_hunk_lines) > 6:
            diff_hunk = "\n".join(
                diff_hunk_lines[:3]
                + ["[...elided for brevity...]"]
                + diff_hunk_lines[-3:]
            )
        elif len(diff_hunk_lines) > 1:
            diff_hunk = "\n".join(diff_hunk_lines)
        else:
            diff_hunk = diff_hunk_lines[0]

        markdown_output.append(
            f"**{user_login}'s comment on:**\n\n{diff_hunk}\n\n**{user_login}'s comment is:**\n{body}\n\n---\n\n"
        )

    return "\n".join(markdown_output)


def get_bot_comments(pr_url: PullRequestURL) -> List[Comment]:
    endpoint = f"/repos/{pr_url.owner}/{pr_url.repo}/issues/{pr_url.number}/comments"
    cmd = f"gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' {endpoint}"

    try:
        result = run_command(cmd)
        comments = json.loads(result)
        return [
            Comment(comment) for comment in comments if comment["user"]["type"] == "Bot"
        ]
    except Exception as e:
        print(f"Error fetching PR comments: {e}")
        return []


def find_linear_issue(pr_url: PullRequestURL) -> Optional[dict]:
    comments = get_bot_comments(pr_url)
    for comment in comments:
        issue = comment.get_linear_issue()
        if issue:
            return {"id": issue.id, "url": issue.url}
    return None
