## Workflow
1. Confirm goal, constraints, and expected output.
2. Use the plan tool for multi-step tasks and keep it updated.
3. Gather required context before edits (code, tests, history, linked PR/issues).
4. Implement in small verifiable steps and validate minimally first, then broadly.
5. Report results, risks, and next actions clearly.

## Sub-agents
- Use independent sub-agents for parallel, specialized, or long-running work.
- Give each sub-agent explicit scope and deliverables.
- Integrate each sub-agent's findings in a distinct section with evidence for traceability.
- For substantial tasks, run a final independent review sub-agent and resolve disagreements before finalizing.

## Review standards
- Prioritize correctness, regressions, security/privacy impact, performance risks, and test gaps.
- Verify PR/comment claims against code and tests.
- Present findings first by severity with file references; if none, state that and note residual risk.

## Incremental documentation
- Keep an incremental working note for non-trivial tasks (user path or repo `backlog/`/`docs/`).
- Update after meaningful steps with evidence, conclusions, and next actions (Markdown checklist).
- Prepend final summary when complete.

## VCS and sources
- Use repo-native VCS (`jj` when configured, otherwise `git`); use `git` for submodules/unsupported flows.
- Do not rewrite or discard others' changes unless explicitly requested.
- For external context, fetch source-of-truth first and cite primary links for non-obvious, high-risk, or time-sensitive claims. Try to use $gh skill for links to code to get Markdown links to GitHub repos.
