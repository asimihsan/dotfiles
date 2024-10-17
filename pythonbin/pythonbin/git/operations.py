# git_operations.py
import os
from dataclasses import dataclass
from typing import List

from git import Repo, GitCommandError


@dataclass
class GitRange:
    start: str  # This could be a tag, commit hash, or other git reference
    end: str = "HEAD"  # Default to HEAD if not specified


@dataclass
class GitCommit:
    hash: str
    author: str
    date: str
    message: str
    files_changed: List[str]


class GitOperations:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or os.getcwd()
        try:
            self.repo = Repo(self.repo_path)
        except GitCommandError:
            raise ValueError(f"No Git repository found at {self.repo_path}")

    def get_current_branch(self):
        return self.repo.active_branch.name

    def get_diff(self, base_branch="origin/master") -> str:
        try:
            self.repo.remotes.origin.fetch()
        except GitCommandError:
            print("Warning: Unable to fetch from remote. Using local reference.")

        try:
            diff = self.repo.git.diff(base_branch)
        except GitCommandError:
            raise ValueError(f"Unable to generate diff against {base_branch}")

        return diff

    def get_changed_files(self, base_branch="origin/master") -> list[str]:
        try:
            self.repo.remotes.origin.fetch()
        except GitCommandError:
            print("Warning: Unable to fetch from remote. Using local reference.")

        try:
            changed_files = self.repo.git.diff("--name-only", base_branch).splitlines()
        except GitCommandError:
            raise ValueError(f"Unable to get changed files against {base_branch}")

        return changed_files

    def get_last_commit_message(self):
        return self.repo.head.commit.message.strip()

    def stage_all_changes(self):
        self.repo.git.add(A=True)

    def commit_changes(self, message):
        try:
            self.repo.git.commit(m=message)
            return True
        except GitCommandError as e:
            print(f"Error committing changes: {str(e)}")
            return False

    def get_commits_in_range(
            self, git_range: GitRange, remote_branch: str = "origin/master"
    ) -> List[GitCommit]:
        """
        Retrieve a list of commits in the specified range that are also present on the remote branch.

        Args:
            git_range (GitRange): The range of commits to consider.
            remote_branch (str): The remote branch to compare against. Defaults to "origin/master".

        Returns:
            List[GitCommit]: A list of GitCommit objects representing commits that are in the specified range
                             and also present on the remote branch.

        Raises:
            ValueError: If there's an error fetching commits or accessing the remote.
        """
        try:
            # Fetch the latest changes from the remote
            self.repo.remotes.origin.fetch()

            # Get the commits in the specified range
            local_commits = list(
                self.repo.iter_commits(f"{git_range.start}..{git_range.end}")
            )

            # Get the commits on the remote branch
            remote_commits = list(self.repo.iter_commits(remote_branch))

            # Filter commits that exist on both local and remote
            merged_commits = [
                commit for commit in local_commits
                if commit.hexsha in {rc.hexsha for rc in remote_commits}
            ]

            return [
                GitCommit(
                    hash=commit.hexsha,
                    author=str(commit.author),
                    date=commit.committed_datetime.isoformat(),
                    message=commit.message.decode("utf-8")
                    if isinstance(commit.message, bytes)
                    else commit.message,
                    files_changed=list(str(k) for k in commit.stats.files.keys()),
                )
                for commit in merged_commits
            ]
        except GitCommandError as e:
            raise ValueError(f"Error fetching commits in range: {str(e)}")
