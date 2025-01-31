#!/usr/bin/env python3
import argparse
import subprocess
from string import Template

from pythonbin.command.command import run_command
from pythonbin.gh.ghlib import find_linear_issue
from pythonbin.gh.ghlib import get_pr_comments, get_pr_description, get_pr_diff, PullRequestURL


def get_ticket_details(ticket):
    return run_command(f"uv run python src/linear_tools/main.py get-issue --issue-id {ticket}", cwd="/Users/asimi/workplace/linear-tools")
    # return run_command(f"jira --comments 100 issue view {ticket} --plain")


def create_prompt(pr_description, pr_diff, pr_comments: str, jira_details=None):
    if jira_details is not None:
        jira_section = "The related Jira ticket details are as follows:\n" + jira_details
    else:
        jira_section = "There are no related Jira ticket details provided."

    template = Template(
        """
    You are a highly capable AI assistant with expertise across many domains. Synthesize a response that uses paragraphs of text and sections, try not to use bullet points unless necessary. Approach this task thoughtfully and methodically:

    1. Take a moment to consider the query and identify any key concepts or higher-level principles that may be relevant.
    2. Break down your approach into logical steps, explaining your reasoning as you go (chain-of-thought).
    3. If multiple perspectives or solutions are possible, explore 2-3 options and compare their merits.
    4. For any claims or conclusions, provide a confidence rating on a scale of 1-5 (1 being least confident, 5 being most confident). Explain the reasoning behind your confidence levels.
    5. If you're unsure about any aspect, acknowledge the uncertainty and explain what additional information would be helpful.
    6. Summarize your key findings or recommendations.

    Remember to maintain a balanced, analytical tone throughout your response.

    Now, please address the following query:

    I need your assistance in reviewing a GitHub Pull Request.

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

    This is going to be a large project so please break this down into a high-level plan before you begin. Then, as you execute the plan, only do so one step at a time, and after each step stop and wait for my feedback. After you get my feedback, re-state the plan and where you are (or if you've finished the plan) then do another small step. Remember to be critical and analytical and verify my goals and requirements and propose your own goals.
    
    If you need to see the contents of files let me know and I can provide them to you.
    
    Your goal is to go point by point in priority order, and for each point act as if you are me and prepare a pull request comment covering what the system is doing, why it is doing it, why it is a problem, and proposed solution.
    """
    )
    return template.substitute(
        pr_description=pr_description,
        pr_diff=pr_diff,
        pr_comments=pr_comments,
        jira_section=jira_section,
    )


def copy_to_clipboard(text):
    process = subprocess.Popen(
        "pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE
    )
    process.communicate(text.encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Review Helper Script")
    parser.add_argument(
        "pr_url", type=str, help="The URL of the Pull Request to review"
    )

    args = parser.parse_args()
    pr_url = args.pr_url

    pull_request_url = PullRequestURL.from_url(pr_url)

    pr_comments = get_pr_comments(pull_request_url)
    pr_description = get_pr_description(pr_url)
    pr_diff = get_pr_diff(pr_url)

    linear_issue = find_linear_issue(pull_request_url)
    if linear_issue:
        linear_details = get_ticket_details(linear_issue["id"])
    else:
        linear_details = None

    prompt = create_prompt(pr_description, pr_diff, pr_comments, linear_details)
    prompt = prompt.strip()
    copy_to_clipboard(prompt)


if __name__ == "__main__":
    main()
