#!/usr/bin/env python3

import argparse
import json
import re
import time
import webbrowser
from dataclasses import dataclass
from os.path import expanduser
from typing import Optional

from pythonbin.gh.ghreview import run_command, PullRequestURL
from pythonbin.git.operations import GitOperations, GitRange


@dataclass
class Config:
    repo: str
    clone_dir: str
    start_tag: str

    def __init__(self, args: argparse.Namespace):
        self.repo = args.repo
        self.clone_dir = expanduser(args.clone_dir)
        self.start_tag = args.start_tag

    @property
    def owner(self):
        return self.repo.split("/")[0]

    @property
    def repo_name(self):
        return self.repo.split("/")[1]


def find_pr_number(repo: str, full_sha: str) -> Optional[int]:
    cmd = f"gh pr list --repo {repo} --search {full_sha} --json number,url --jq '.[0]' --state merged"
    try:
        result = run_command(cmd)
        pr_data = json.loads(result)
        if pr_data:
            return pr_data["number"]
        return None
    except Exception as e:
        print(f"Error finding PR: {e}")
        return None


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


def get_bot_comments(pr_url: PullRequestURL) -> list[Comment]:
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


def main(config: Config):
    git_ops = GitOperations(config.clone_dir)
    commits = git_ops.get_commits_in_range(GitRange(start=config.start_tag))
    for commit in commits:
        time.sleep(1)

        pr_number = find_pr_number(config.repo, commit.hash)
        if not pr_number:
            print(f"No PR found for commit: {commit.hash}")
            continue

        pr_url = PullRequestURL(
            original_url=f"https://github.com/{config.repo}/pull/{pr_number}",
            owner=config.owner,
            repo=config.repo_name,
            number=pr_number,
        )
        bot_comments = get_bot_comments(pr_url)

        print(f"\n--- Commit: {commit.hash} ---")
        print(f"Message: {commit.message.strip()}")
        print(f"PR: {pr_url.original_url}")
        print(f"Author: {commit.author}")
        print(f"Date: {commit.date}")
        if not bot_comments:
            print("No bot comments found")
        else:
            linear_issues = [comment.get_linear_issue() for comment in bot_comments]

            print("Linear Issues:")
            for idx, issue in enumerate(linear_issues, 1):
                if issue:
                    print(f"  {idx}. {issue.url} ({issue.id})")
                    webbrowser.open(issue.url)
                else:
                    print(f"  {idx}. No Linear issue found")
        print("---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find out Linear issues from Git starting tag"
    )
    parser.add_argument("repo", help="The GitHub repository in the format 'owner/repo'")
    parser.add_argument("clone_dir", help="The directory the repository is cloned to")
    parser.add_argument("start_tag", help="The starting tag to find Linear issues from")
    args = Config(parser.parse_args())

    main(args)
