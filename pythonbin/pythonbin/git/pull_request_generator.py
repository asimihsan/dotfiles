# git/pull_request_generator.py
from dataclasses import dataclass
from typing import Callable, List

from pythonbin.git.commit_message_generator import generate_commit_message
from pythonbin.llm.client import LLMClient, Response, LLMFunctionTool
from pythonbin.git.operations import GitOperations

PR_TEMPLATE = """
## What is the change?
> _(Summarize the change and affected system parts.)_

## Why is the change necessary?
> _(Describe the problem and its impact. How do your changes address it? Link to Jira tickets for context.)_

## How has this change been tested?
- [ ] New tests added (describe briefly)
- [ ] Existing tests apply (list relevant tests)
- [ ] No testing required (explain why)

> - _(If automated tests are not possible, describe manual testing steps.)_
> - _(For functional changes, describe what QA testing is needed for stage.)_

## Related Tickets
> _(Link to related Jira tickets or documentation.)_
"""


def get_diff_wrapper(git_ops: GitOperations, base_branch: str) -> Callable[[], str]:
    def get_diff() -> str:
        """
        Retrieve the Git diff against the specified base branch.

        Returns
        -------
        str
            A string representation of the Git diff.
        """
        return git_ops.get_diff(base_branch)

    return get_diff


def get_changed_files_wrapper(git_ops: GitOperations, base_branch: str) -> Callable[[], List[str]]:
    def get_changed_files() -> List[str]:
        """
        Retrieve a list of changed files compared to the specified base branch.

        Returns
        -------
        List[str]
            A list of changed file paths.
        """
        return git_ops.get_changed_files(base_branch)

    return get_changed_files


def generate_pull_request_description(model: str, git_ops: GitOperations, commit_message: str,
                                      base_branch: str = "origin/master") -> str:
    tools = [
        LLMFunctionTool(
            name="get_diff",
            callable=get_diff_wrapper(git_ops, base_branch),
        ),
        LLMFunctionTool(
            name="get_changed_files",
            callable=get_changed_files_wrapper(git_ops, base_branch),
        ),
    ]

    llm_client = LLMClient(model, tools)

    system_message = """You are an AI assistant specialized in generating comprehensive and informative pull request descriptions. 
    Your task is to analyze the provided Git diff, changed files, and commit message to create a pull request description that follows the given template."""

    user_message = f"""Please generate a pull request description based on the following information:
    1. The Git diff (which you can retrieve using the get_diff function)
    2. The list of changed files (which you can retrieve using the get_changed_files function)
    3. The commit message: {commit_message}

    Use the following template to structure your response:

    {PR_TEMPLATE}

    Fill in the template with relevant information based on the changes. Be specific and informative, and make sure to address all sections of the template."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    response: Response = llm_client.generate_response(messages)

    return response.response.strip()


@dataclass
class Args:
    model: str = "gpt-4o"
    base_branch: str = "origin/master"
    directory: str = "."


def parse_args() -> Args:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Generate a Git commit message and pull request description based on the provided diff.")
    parser.add_argument("--model", type=str, default="gpt-4",
                        help="The LLM model to use for generating the commit message and PR description.")
    parser.add_argument("--base-branch", type=str, default="origin/master",
                        help="The base branch to compare the diff against.")
    parser.add_argument("--directory", type=str, default=".", help="The directory of the Git repository.")

    args = parser.parse_args()
    return Args(model=args.model, base_branch=args.base_branch, directory=os.path.abspath(args.directory))


if __name__ == "__main__":
    args = parse_args()
    git_ops = GitOperations(repo_path=args.directory)

    # First, generate the commit message
    commit_message = generate_commit_message(args.model, git_ops, args.base_branch)
    print(f"Generated commit message:\n\n{commit_message}\n")

    # Then, generate the pull request description
    pr_description = generate_pull_request_description(args.model, git_ops, commit_message, args.base_branch)
    print(f"Generated pull request description:\n\n{pr_description}")
