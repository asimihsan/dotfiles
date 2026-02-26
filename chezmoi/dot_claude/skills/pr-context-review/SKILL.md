---
name: pr-context-review
description: Review GitHub pull requests with both code-review rigor and pedagogical system context (problem framing, architecture, and data flow). Use when the user wants PR analysis tied to linked Linear issues/comments, related PRs, and an incrementally maintained Markdown analysis document with explicit evidence and final prepended conclusions.
---

# PR Context Review

## Overview

Use this skill when a user wants more than "LGTM/changes requested" feedback. Produce a review that explains where the PR fits in the system, what problem it solves, and whether review-thread claims are actually substantiated by code.

## Required Inputs

Set these two variables at the start of execution:

- `DOC_OUTPUT_PATH`: Absolute or `~` path to the analysis Markdown file.
- `PR_URL`: Full GitHub PR URL.

Example:

```text
DOC_OUTPUT_PATH=~/workplace/llm/ldp-2588/2026-02-26_analysis.md
PR_URL=https://github.com/LevelHome/platform-fleet-service/pull/258
```

## Skill Stack And Order

Use these skills in order:

1. `$use-gh-cli`: Pull PR description, diff, comments, and review threads.
2. `$using-linear`: Pull linked Linear issue(s), comments, related issues/projects, and linked PRs.
3. `$jujutsu`: Inspect local repository history/diffs when the repo has `.jj`.

Use independent sub-agents for parallel analysis tracks, then run a final independent QA sub-agent to challenge and refine the output.

## Execution Workflow

1. Initialize work tracking.
   - Create or update `DOC_OUTPUT_PATH`.
   - Keep an always-current checklist for scope, evidence, findings, open questions, and next steps.
2. Gather GitHub PR evidence with `$use-gh-cli`.
   - Run required preflight (`gh --help && gh auth status`, then `gh pr --help`).
   - Pull PR description, comments, review threads, and latest diff.
   - Focus on existing comment threads and author responses.
3. Gather product context with `$using-linear`.
   - Run `linearis usage` once before first Linear command.
   - Fetch linked issue(s), issue comments, related issues, related projects.
   - For related issues, fetch linked PR descriptions/comments for additional context.
4. Inspect local service code and history with `$jujutsu`.
   - Search relevant repos in `~/workplace` and current working directory.
   - Use `jj st`, `jj log`, and `jj diff` where applicable.
5. Run independent sub-agents in parallel.
   - Suggested split:
     - Agent A: PR diff + comment-thread verification.
     - Agent B: system context/data flow pedagogical scaffold.
     - Agent C: Linear + related issue/PR context synthesis.
   - After each agent completes, add its findings/evidence/artifacts to `DOC_OUTPUT_PATH` immediately.
6. Run a final independent QA sub-agent.
   - Have it critique coherence, evidence quality, contradictions, and missing checks.
   - Iterate until no material gaps remain.
7. Finalize deliverables.
   - Prepend final analysis at top of `DOC_OUTPUT_PATH`.
   - Ensure the doc remains chronologically incremental below the prepended final section.

## Documentation Contract

Treat `DOC_OUTPUT_PATH` as the running source of truth.

- Update it after every major step.
- Preserve incremental traceability: what was checked, why, and what was concluded.
- Use markdown checklists (`- [ ]`, `- [x]`) for active tracking.
- Include a subsection per completed sub-agent with:
  - Goal
  - Evidence gathered
  - Findings
  - Artifacts/links
  - Remaining questions

Use GitHub Markdown links to repo files when possible.

## Analysis Quality Bar

- Separate facts from inference explicitly.
- Verify whether comment-thread claims are reflected in the current diff.
- State where you agree/disagree with comments, and why.
- Include citations/links for key assertions.
- Keep the final analysis coherent and logically structured.

## Prompt Template

Use the template in `references/review-prompt-template.md` and replace:

- `{{DOC_OUTPUT_PATH}}`
- `{{PR_URL}}`

before executing.
