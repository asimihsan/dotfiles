---
name: use-gh-cli
description: Use the GitHub CLI (`gh`) to manage GitHub repositories, pull requests, issues, search, releases, workflows, and API calls from the shell. Use when the user asks to run `gh` commands, troubleshoot GitHub CLI behavior, or automate PR/issue/release/Actions tasks (including `gh api`).
---

# Use Gh Cli

## Overview
Use this skill to run `gh` safely and consistently with mandatory help/auth checks and a catalog of common workflows.

## Required Preflight (Always)
1. Run `gh --help && gh auth status` before any `gh` usage. If auth is missing or expired, stop and ask the user to authenticate.
2. Before any subcommand, run help for its command group, e.g. `gh pr --help`. If needed, also run `gh pr create --help` or similar to confirm flags and behavior.

## Core Workflow
1. Confirm repository context. Prefer running inside the repo. If not, use `-R OWNER/REPO`.
2. Run the command-group help and verify flags.
3. Execute the command with explicit flags; avoid guessing.

## Writing PR/Issue Bodies And Comments (Required)
- Whenever posting a PR description, PR comment, issue description, or issue comment, **do not** inline the body text.
- First write the content to a file using a heredoc, then pass the file to `gh` (e.g., `--body-file`).
- Ensure all bodies/comments are Markdown with clear logical structure: short intro, headings, and concise lists. Avoid walls of text.
- Always prefix the body with a first, standalone paragraph: `(This is from an LLM)`
- Recommended pattern:
  - Create: `cat <<'EOF' > /tmp/gh-body.md ... EOF`
  - Use: `gh pr create ... --body-file /tmp/gh-body.md` or `gh pr comment <pr> --body-file /tmp/gh-body.md`

## Typical Tasks (High-Level Sketch)

### Repo + Auth
- View repo: `gh repo view`
- Clone: `gh repo clone OWNER/REPO`
- Fork: `gh repo fork`
- Set default repo: `gh repo set-default`

### Pull Requests
- List/status: `gh pr list`, `gh pr status`
- View/diff: `gh pr view <pr>`, `gh pr diff <pr>`
- Create: `gh pr create --fill`
- Checkout: `gh pr checkout 353`
- Comment (general): `gh pr comment <pr> --body "..."`
- Merge: `gh pr merge <pr>`
- Checks: `gh pr checks <pr>`

### Issues
- List/view: `gh issue list`, `gh issue view <issue>`
- Create: `gh issue create`
- Comment/close: `gh issue comment <issue> --body "..."`, `gh issue close <issue>`

### Search
- General: `gh search repos|issues|prs|code <query>`
- Excluding qualifiers: use `--` before the query on Unix-like shells:
  `gh search issues -- "my query -label:bug"`
- On PowerShell: `gh --% search issues -- "my query -label:bug"`

### Actions (Workflows & Runs)
- List workflows: `gh workflow list`
- Run workflow: `gh workflow run <workflow>`
- List runs: `gh run list`
- Watch run: `gh run watch <run-id>`
- View logs: `gh run view <run-id> --log`

### Releases
- List/view: `gh release list`, `gh release view <tag>`
- Create: `gh release create <tag>`
- Download: `gh release download <tag>`

### API + Inline PR Comments (High-Level)
- Use `gh api` for endpoints not covered by `gh pr comment` (e.g., inline diff comments).
- Require `commit_id` (PR head SHA), `path`, `line`, and `side` for inline comments.
- Get head SHA with: `gh pr view <pr> --json headRefOid --jq .headRefOid`
- Use endpoint: `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments`
- Include `start_line` and `start_side` for range comments.
- Reply to an inline comment thread with:
  `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies`
- Alternatively, use `in_reply_to` when creating a comment.

## Learn More
- Use `gh <command> <subcommand> --help` for details.
- Read the manual at https://cli.github.com/manual
- See exit codes: `gh help exit-codes`
- Accessibility: `gh help accessibility`
