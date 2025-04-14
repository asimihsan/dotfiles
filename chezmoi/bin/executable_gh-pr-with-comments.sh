#!/bin/bash

set -euo pipefail

# Check if first argument is a URL
if [[ "$1" == http* ]]; then
  # Parse URL to extract repository and PR number
  if [[ "$1" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
    REPO="$OWNER/$REPO_NAME"
  else
    echo "Error: Invalid GitHub PR URL format. Expected: https://github.com/OWNER/REPO/pull/NUMBER"
    exit 1
  fi
else
  # Original usage: first arg is PR number, second arg is repo
  if [ $# -lt 2 ]; then
    echo "Error: When providing PR number directly, you must also specify the repository."
    echo "Usage: $0 PR_NUMBER OWNER/REPO"
    echo "   or: $0 https://github.com/OWNER/REPO/pull/NUMBER"
    exit 1
  fi
  PR_NUMBER=$1
  REPO=$2
fi

# Get PR info
PR_INFO=$(gh pr view "$PR_NUMBER" --json title,number,author,state,body)
PR_TITLE=$(echo "$PR_INFO" | jq -r '.title')
PR_AUTHOR=$(echo "$PR_INFO" | jq -r '.author.login')
PR_STATE=$(echo "$PR_INFO" | jq -r '.state')
PR_DESCRIPTION=$(echo "$PR_INFO" | jq -r '.body')

# Get both types of comments
REVIEW_COMMENTS=$(gh api repos/$REPO/pulls/"$PR_NUMBER"/comments)
ISSUE_COMMENTS=$(gh api repos/$REPO/issues/"$PR_NUMBER"/comments)

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
echo "## Regular Comments"
echo "$ISSUE_COMMENTS" | jq -r '.[] | "### Comment by \(.user.login) on \(.created_at)\n\n\(.body)\n\n"'
echo ""
echo "## Review Comments"
echo "$REVIEW_COMMENTS" | jq -r '.[] | "### Comment on file `\(.path)` line \(.line)\n**\(.user.login)** commented on \(.created_at):\n\n\(.body)\n\n```\n\(.diff_hunk)\n```\n"'
