import json
import subprocess
from urllib.parse import urlparse

from pydantic import BaseModel

from pythonbin.command.command import run_command


class PullRequestURL(BaseModel):
    original_url: str
    owner: str
    repo: str
    number: int

    @classmethod
    def from_url(cls, url: str) -> "PullRequestURL":
        """
        :param url: GitHub PR URL, e.g. https://github.com/LevelHome/LevelServer/pull/3940
        :return: PullRequestURL instance
        """

        elems = urlparse(url)

        if elems.hostname != "github.com":
            raise ValueError(f"Invalid hostname: {elems.hostname}")

        path = elems.path
        path_elems = path.split("/")

        # if it ends with "files", we can ignore it
        if path_elems[-1] == "files":
            path_elems = path_elems[:-1]

        if len(path_elems) != 5:
            raise ValueError(f"Invalid path: {path}")

        owner = path_elems[1]
        repo = path_elems[2]
        number = int(path_elems[4])

        return cls(original_url=url, owner=owner, repo=repo, number=number)





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


def get_pr_comments(pr_url: "PullRequestURL") -> str:
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
