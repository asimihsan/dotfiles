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

Use `mktemp` to avoid output file collisions. Always redirect stderr to avoid polluting context with intermediate reasoning.

```bash
OUTPUT_FILE=$(mktemp /tmp/codex-XXXXXX)
codex exec --full-auto -o "$OUTPUT_FILE" "Your verification prompt here" 2>/dev/null
cat "$OUTPUT_FILE"
```

Run in background with 15-minute timeout for long analyses.
