#!/usr/bin/env python3

import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Optional, List

from pythonbin.gh.ghlib import PullRequestURL
from pythonbin.git.operations import GitOperations, GitRange
from pythonbin.command.command import run_command
from pythonbin.gh.ghlib import get_bot_comments


@dataclass
class ChangelogEntry:
    commit_hash: str
    title: str
    pr_url: Optional[PullRequestURL] = None
    linear_issue: Optional[dict] = None

    def __post_init__(self):
        # Remove PR numbers from the end of titles e.g. "(#1234)"
        self.title = re.sub(r"\s+\(#\d+\)$", "", self.title)

    def as_markdown(self) -> str:
        parts = ["- "]

        if self.linear_issue:
            issue_id = self.linear_issue["id"]
            issue_url = self.linear_issue["url"]
            parts.append(f"[{issue_id}]({issue_url}) ")

        if self.pr_url:
            pr_num = self.pr_url.number
            parts.append(f"[PR {pr_num}]({self.pr_url.original_url}) ")

        parts.append(f"{self.title}")
        parts.append(
            f"\n  [{self.commit_hash[:7]}]"
            f"(https://github.com/LevelHome/LevelServer/commit/{self.commit_hash})"
        )

        return "".join(parts)


def generate_changelog(repo_path: str, start_ref: str) -> List[ChangelogEntry]:
    git_ops = GitOperations(repo_path=repo_path)
    commits = git_ops.get_commits_in_range(GitRange(start=start_ref))
    entries = []

    repo = "LevelHome/LevelServer"  # TODO: Make configurable

    for commit in commits:
        pr_url = find_pr_url(repo, commit.hash)
        linear_issue = None
        if pr_url:
            linear_issue = find_linear_issue(pr_url)

        entry = ChangelogEntry(
            commit_hash=commit.hash,
            title=commit.message.split("\n")[0].strip(),
            pr_url=pr_url,
            linear_issue=linear_issue,
        )
        entries.append(entry)

    return entries


def find_pr_url(repo: str, commit_hash: str) -> Optional[PullRequestURL]:
    cmd = f"gh pr list --repo {repo} --search {commit_hash} --json number,url --jq '.[0]' --state merged"
    try:
        result = json.loads(run_command(cmd))
        if result:
            return PullRequestURL.from_url(result["url"])
    except Exception as e:
        print(f"Error finding PR for commit {commit_hash}: {e}")
    return None


def find_linear_issue(pr_url: PullRequestURL) -> Optional[dict]:
    comments = get_bot_comments(pr_url)
    for comment in comments:
        issue = comment.get_linear_issue()
        if issue:
            return {"id": issue.id, "url": issue.url}
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate a formatted changelog")
    parser.add_argument(
        "--repo", required=True, help="Path to the repository to generate changelog"
    )
    parser.add_argument(
        "--start", required=True, help="Git reference to start changelog from"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.repo):
        raise ValueError(f"Invalid repository path: {args.repo}")

    entries = generate_changelog(args.repo, args.start)
    for entry in entries:
        print(entry.as_markdown())


if __name__ == "__main__":
    main()
