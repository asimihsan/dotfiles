#!/bin/bash

set -euo pipefail

PR_NUMBER=$1
REPO="LevelHome/LevelServer"

# Get PR info
PR_INFO=$(gh pr view "$PR_NUMBER" --json title,number,author,state,body)
PR_TITLE=$(echo "$PR_INFO" | jq -r '.title')
PR_AUTHOR=$(echo "$PR_INFO" | jq -r '.author.login')
PR_STATE=$(echo "$PR_INFO" | jq -r '.state')
PR_DESCRIPTION=$(echo "$PR_INFO" | jq -r '.body')

# Get comments
COMMENTS=$(gh api repos/$REPO/pulls/"$PR_NUMBER"/comments)

# Create markdown output
echo "# PR #$PR_NUMBER: $PR_TITLE"
echo "- Author: $PR_AUTHOR"
echo "- State: $PR_STATE"
echo ""
echo "## Description"
echo "$PR_DESCRIPTION"
echo ""
echo "## Diff"
echo '```diff'
gh pr diff "$PR_NUMBER"
echo '```'
echo ""
echo "## Review Comments"
echo "$COMMENTS" | jq -r '.[] | "### Comment on file `\(.path)` line \(.line)\n**\(.user.login)** commented on \(.created_at):\n\n\(.body)\n\n```\n\(.diff_hunk)\n```\n"'
