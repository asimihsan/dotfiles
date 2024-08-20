# git_operations.py
import os
from git import Repo, GitCommandError


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
