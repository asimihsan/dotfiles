#!/usr/bin/env python3

import subprocess
import re

def get_commits(tag):
    # Get the list of commits from the specified tag to HEAD
    cmd = f"git log {tag}..HEAD --oneline"
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    return output.strip().split('\n')

def process_commits(commits):
    markdown = []
    for commit in commits:
        # Extract the commit hash and message
        match = re.match(r'(\w+)\s+(.+)', commit)
        if match:
            hash, message = match.groups()

            # Check if the commit message contains a PR number
            pr_match = re.search(r'\(#(\d+)\)$', message)
            if pr_match:
                pr_number = pr_match.group(1)
                # Remove the PR number from the message
                message = re.sub(r'\s*\(#\d+\)$', '', message)
                # Create a Markdown link for the PR
                pr_link = f"[#{pr_number}](https://github.com/LevelHome/LevelServer/pull/{pr_number})"
                markdown.append(f"* {message} ({pr_link})")
            else:
                markdown.append(f"* {message}")

    return '\n'.join(markdown)

def main():
    tag = input("Enter the starting tag: ")
    commits = get_commits(tag)
    markdown = process_commits(commits)
    print("\nGenerated Markdown:\n")
    print(markdown)

if __name__ == "__main__":
    main()
