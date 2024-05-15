#!/usr/bin/env python3

import argparse
import datetime
import os
import subprocess
import sys

from git import Repo
from git.exc import GitCommandError


def is_go_repo(repo_path):
    return all([os.path.isfile(os.path.join(repo_path, f)) for f in ["go.mod", "go.sum"]])


def update_go_dependencies(repo_path):
    try:
        subprocess.run(["go", "get", "-u", "./..."], cwd=repo_path, check=True)
        subprocess.run(["go", "mod", "tidy"], cwd=repo_path, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update Go dependencies in {repo_path}: {e}", file=sys.stderr)
        raise


def commit_and_push(repo, branch_name):
    try:
        repo.git.add(all=True)
        repo.index.commit("Update dependencies")
        repo.git.push("--set-upstream", "origin", branch_name, "--force-with-lease")
    except GitCommandError as e:
        print(f"Failed to commit and push changes: {e}", file=sys.stderr)
        raise


def create_pull_request(repo_path, base_branch, head_branch):
    try:
        subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                "Update dependencies",
                "--body",
                "Automated update of dependencies",
                "--base",
                base_branch,
                "--head",
                head_branch,
            ],
            cwd=repo_path,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to create pull request: {e}", file=sys.stderr)
        raise


def wait_for_checks(repo_path, pr_branch):
    try:
        # Wait for checks to complete
        while True:
            result = subprocess.run(
                ["gh", "pr", "checks", pr_branch, "--json", "status", "--jq", ".status"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            status = result.stdout.strip()

            if status == "COMPLETED":
                print("All checks passed!")
                return
            elif status in ["QUEUED", "IN_PROGRESS"]:
                print("Waiting for checks to complete...")
                subprocess.run(["sleep", "10"])
            else:
                print(f"One or more checks failed. Please review: {pr_url}")
                sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Failed to check PR status: {e}", file=sys.stderr)
        raise


def run_main():
    parser = argparse.ArgumentParser(description="Update dependencies in a Git repository and create a pull request.")
    parser.add_argument("local_repo_path", help="Path to the local Git repository")
    parser.add_argument("-b", "--branch", help="Name of the branch to create (default: update-deps-<timestamp>)",
                        default=None)
    args = parser.parse_args()

    local_repo_path = args.local_repo_path

    if not os.path.isdir(local_repo_path):
        print(f"Local repository path '{local_repo_path}' does not exist or is not a directory.")
        sys.exit(1)

    repo = Repo(local_repo_path)
    if repo.is_dirty() or repo.untracked_files:
        print("Repository has uncommitted changes. Please commit or stash them before running this script.")
        sys.exit(1)

    repo.git.checkout("main")

    repo.remote().fetch()
    repo.git.rebase("origin/main")

    base_branch = repo.active_branch.tracking_branch().name.split("/")[-1]
    branch_name = args.branch or f"update-deps-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    # if branch already exists, delete it
    if branch_name in [b.name for b in repo.branches]:
        repo.git.branch("-D", branch_name)

    repo.git.checkout("-b", branch_name)

    if is_go_repo(local_repo_path):
        update_go_dependencies(local_repo_path)

    commit_and_push(repo, branch_name)

    create_pull_request(local_repo_path, base_branch, branch_name)

    wait_for_checks(local_repo_path, branch_name)


if __name__ == "__main__":
    run_main()
