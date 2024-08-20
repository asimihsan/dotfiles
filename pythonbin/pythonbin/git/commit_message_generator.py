# git/commit_message_generator.py
import os
from dataclasses import dataclass
from typing import Callable

from pythonbin.git.operations import GitOperations
from pythonbin.llm.client import LLMClient, Response, LLMFunctionTool


def get_diff_wrapper(git_ops: GitOperations, base_branch: str) -> Callable[[], str]:
    def get_diff() -> str:
        """
        Retrieve the Git diff against the specified base branch.

        Parameters
        ----------

        None

        Returns
        -------

        str
            A string representation of the Git diff.
        """

        return git_ops.get_diff(base_branch)

    return get_diff


def generate_commit_message(model: str, git_ops: GitOperations, base_branch: str = "origin/master") -> str:
    tools = [
        LLMFunctionTool(
            name="get_diff",
            callable=get_diff_wrapper(git_ops, base_branch),
        ),
    ]

    llm_client = LLMClient(model, tools)

    system_message = """You are an AI assistant specialized in generating concise and informative Git commit messages. 
    Your task is to analyze the provided Git diff and create a commit message that accurately summarizes the changes."""

    user_message = """Please generate a commit message based on the following Git diff. 
    The commit message should be concise (preferably under 50 characters) but informative, 
    summarizing the main changes in the diff. If there are multiple significant changes, 
    you may use a multi-line commit message with a brief summary line followed by bullet points for details.
    The Git commit message must adhere to conventional commit message standards."""

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
    directory: str = os.getcwd()


def parse_args() -> Args:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Git commit message based on the provided diff.")
    parser.add_argument("--model", type=str, default="gpt-4",
                        help="The LLM model to use for generating the commit message.")
    parser.add_argument("--base-branch", type=str, default="origin/master",
                        help="The base branch to compare the diff against.")
    parser.add_argument("--directory", type=str, default=os.getcwd(), help="The directory of the Git repository.")

    args = parser.parse_args()
    return Args(model=args.model, base_branch=args.base_branch, directory=args.directory)


if __name__ == "__main__":
    args = parse_args()
    git_ops = GitOperations(repo_path=args.directory)
    commit_message = generate_commit_message(args.model, git_ops)
    print(f"Generated commit message:\n\n{commit_message}")
