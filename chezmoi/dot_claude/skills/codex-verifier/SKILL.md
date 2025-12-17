---
name: codex-verifier
description: Use OpenAI Codex CLI as a second-opinion agent for verification, exploration, and analysis tasks. Invoke when the user asks to verify assumptions, get a second opinion, cross-check analysis, explore alternatives, or use Codex for read-only analysis. Triggers on phrases like "verify with codex", "get a second opinion", "cross-check", "have codex analyze", "explore with codex".
---

# Codex Verifier

Delegates verification, analysis, and exploration tasks to OpenAI's Codex CLI as a second-opinion agent.

## First: Get Current CLI Syntax

Run this at the start to ensure you have current options:

```bash
codex exec --help
```

## Command Pattern

Remember that the prompt should contain all necessary context for the task at hand; filepaths, code snippets, previously run commands, the path to the plan you are currently working on, etc.

Use `mktemp` to avoid output file collisions. Always redirect stderr to avoid polluting context with intermediate reasoning. Run `codex` in the background with a 15-minute timeout. Do not stop waiting for codex if it takes a long time.

```bash
OUTPUT_FILE=$(mktemp /tmp/codex-XXXXXX)
codex exec --model gpt-5.2 --dangerously-bypass-approvals-and-sandbox -o "$OUTPUT_FILE" "Your verification prompt here" 2>/dev/null
cat "$OUTPUT_FILE"
```


