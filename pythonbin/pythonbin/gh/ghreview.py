#!/usr/bin/env python3
import json
import re
import subprocess
from string import Template
from urllib.parse import urlparse

from pydantic import BaseModel


class CommandFailedException(Exception):
    def __init__(self, command, message):
        self.command = command
        self.message = f"Command failed: {command}\n{message}"
        super().__init__(self.message)


def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        raise CommandFailedException(command, result.stderr.decode('utf-8'))
    return result.stdout.decode('utf-8')


def get_pr_description(pr_url):
    return run_command(f"/opt/homebrew/bin/gh pr view {pr_url} --json \"body,comments\" -q .body")


def get_pr_diff(pr_url, exclude_files=None):
    if exclude_files is None:
        exclude_files = ['poetry.lock', 'pyproject.toml']  # Default files to ignore
    diff_text = run_command(f"/opt/homebrew/bin/gh pr diff {pr_url}")
    filtered_diff = []
    diff_lines = diff_text.split('\n')
    skip = False
    for line in diff_lines:
        if line.startswith('diff --git'):
            skip = any(file_name in line for file_name in exclude_files)
        if not skip:
            filtered_diff.append(line)
    return '\n'.join(filtered_diff)


def get_pr_comments(pr_url: 'PullRequestURL') -> str:
    # Construct the GitHub API endpoint for PR comments
    endpoint = f"/repos/{pr_url.owner}/{pr_url.repo}/pulls/{pr_url.number}/comments"

    # Call the GitHub CLI
    result = subprocess.run(
        [
            "/opt/homebrew/bin/gh",
            "api",
            "-H", "Accept: application/vnd.github+json",
            "-H", "X-GitHub-Api-Version: 2022-11-28",
            endpoint,
        ],
        capture_output=True,
        text=True
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
        user_login = comment['user']['login']
        diff_hunk = comment['diff_hunk']
        body = comment['body']

        # Truncate the diff_hunk if it's too long
        diff_hunk_lines = diff_hunk.split('\n')
        if len(diff_hunk_lines) > 6:
            diff_hunk = '\n'.join(diff_hunk_lines[:3] + ['[...elided for brevity...]'] + diff_hunk_lines[-3:])
        elif len(diff_hunk_lines) > 1:
            diff_hunk = '\n'.join(diff_hunk_lines)
        else:
            diff_hunk = diff_hunk_lines[0]

        markdown_output.append(
            f"**{user_login}'s comment on:**\n\n{diff_hunk}\n\n**{user_login}'s comment is:**\n{body}\n\n---\n\n")

    return '\n'.join(markdown_output)


def find_jira_tickets(description):
    return re.findall(r'\b[A-Z]{2,}-\d+\b', description)


def get_jira_details(ticket):
    return run_command(f"/opt/homebrew/bin/jira --comments 100 issue view {ticket} --plain")


def create_prompt(pr_description, pr_diff, pr_comments: str, jira_details=None):
    jira_section = "- The related Jira ticket details are as follows:\n$jira_details" if jira_details else "- There are no related Jira ticket details provided."

    template = Template("""
    Act like a Senior Software Engineer. I need your assistance in reviewing a GitHub Pull Request.

    Here's what you need to know:
    - The PR description is as follows:
    $pr_description

    - The PR diff is as follows:
    $pr_diff

    $jira_section
    
    - The PR comments are as follows:
    $pr_comments

    Please prioritize any issues you find and propose comments. You can comment generally about the whole PR or specifically about files and line numbers. If you have any questions, let me know before starting.
                        
    Your goal is the give a high-level impression first, but then dive into the details for specific files and lines. If you need to see other files in the project ask me.
    """)
    return template.substitute(
        pr_description=pr_description,
        pr_diff=pr_diff,
        pr_comments=pr_comments,
        jira_section=jira_section
    )


def copy_to_clipboard(text):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))


class PullRequestURL(BaseModel):
    original_url: str
    owner: str
    repo: str
    number: int

    @classmethod
    def from_url(cls, url: str) -> 'PullRequestURL':
        """
        :param url: GitHub PR URL, e.g. https://github.com/LevelHome/LevelServer/pull/3940
        :return: PullRequestURL instance
        """

        elems = urlparse(url)

        if elems.hostname != 'github.com':
            raise ValueError(f'Invalid hostname: {elems.hostname}')

        path = elems.path
        path_elems = path.split('/')

        # if it ends with "files", we can ignore it
        if path_elems[-1] == "files":
            path_elems = path_elems[:-1]

        if len(path_elems) != 5:
            raise ValueError(f'Invalid path: {path}')

        owner = path_elems[1]
        repo = path_elems[2]
        number = path_elems[4]

        return cls(
            original_url=url,
            owner=owner,
            repo=repo,
            number=number
        )


def main(pr_url: str):
    pull_request_url = PullRequestURL.from_url(pr_url)

    pr_comments = get_pr_comments(pull_request_url)
    pr_description = get_pr_description(pr_url)
    pr_diff = get_pr_diff(pr_url)
    jira_tickets = find_jira_tickets(pr_description)

    try:
        jira_details = "\n\n".join([get_jira_details(ticket) for ticket in jira_tickets]) if jira_tickets else None
    except:
        jira_details = None

    prompt = create_prompt(pr_description, pr_diff, pr_comments, jira_details)
    prompt = prompt.strip()
    copy_to_clipboard(prompt)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python review_helper.py <PR_URL>")
    else:
        main(sys.argv[1])
