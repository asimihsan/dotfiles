---
name: codex-verifier
description: Use OpenAI Codex CLI as a second-opinion agent for verification, exploration, and analysis tasks. Invoke when the user asks to verify assumptions, get a second opinion, cross-check analysis, explore alternatives, or use Codex for read-only analysis. Triggers on phrases like "verify with codex", "get a second opinion", "cross-check", "have codex analyze", "explore with codex".
---

# Codex Verifier

This skill enables Claude Code to delegate verification, analysis, and exploration tasks to OpenAI's Codex CLI as a second-opinion agent.

Increase command timeout to 15 minutes when using Codex CLI.

Run `codex` in the background and use `sleep 60` polling to check if it's done.

Use `-o`/`--output-last-message` to write the final message to a file in addition to stdout redirection.

## Prerequisites

Verify Codex CLI is installed and authenticated:

```bash
codex --version
codex login status
```

If not installed: `npm i -g @openai/codex` or `brew install codex`

## Context Efficiency

**Critical**: Codex streams verbose progress to stderr and only the final message to stdout. Always redirect stderr to /dev/null to avoid polluting Claude's context with intermediate reasoning, file reads, and tool calls.

```bash
# CORRECT - captures only final message
codex --ask-for-approval never --sandbox workspace-write exec "Your prompt" 2>/dev/null

# WRONG - captures entire trajectory (all reasoning, file reads, commands)
codex --ask-for-approval never --sandbox workspace-write exec --json "Your prompt"

## Core Use Cases

### 1. Verification / Second Opinion

Cross-check Claude's analysis or assumptions with an independent model:

```bash
codex --ask-for-approval never --sandbox workspace-write exec --model gpt-5.2 --config 'model_reasoning_effort=xhigh' \
  "Verify this assumption: [ASSUMPTION]. Review the codebase and confirm or refute with evidence." 2>/dev/null
```

### 2. Exploration / Discovery

Explore unfamiliar code or patterns:

```bash
codex --ask-for-approval never --sandbox workspace-write exec --model gpt-5.2 --config 'model_reasoning_effort=xhigh' \
  "Analyze the authentication flow in this codebase. Trace from login endpoint to session storage." 2>/dev/null
```

### 3. Architectural Analysis

Get independent architectural assessment:

```bash
codex --ask-for-approval never --sandbox workspace-write exec --model gpt-5.2 --config 'model_reasoning_effort=xhigh' \
  "Review the architecture and identify potential bottlenecks or anti-patterns." 2>/dev/null
```

### 4. Test Coverage Validation

Verify test coverage assumptions:

```bash
codex --ask-for-approval never --sandbox workspace-write exec --model gpt-5.2 --config 'model_reasoning_effort=xhigh' \
  "Analyze test coverage for the payment module. Identify untested edge cases." 2>/dev/null
```

## Command Patterns

### Basic Pattern (Recommended)

Always use ` for verification tasks and redirect stderr:

```bash
codex --ask-for-approval never --sandbox workspace-write exec "PROMPT" 2>/dev/null
```

### Output to File

`-o`/`--output-last-message` writes the final message to a file in addition to stdout redirection. This is useful when you need to preserve the analysis for later reference.

```bash
codex --ask-for-approval never --sandbox workspace-write exec -o /tmp/codex-analysis.md \
  "PROMPT" 2>/dev/null
cat /tmp/codex-analysis.md
```

### Specific Directory Analysis

Target a specific subdirectory:

```bash
codex --ask-for-approval never --sandbox workspace-write exec --config ./src/auth \
  "Analyze security patterns in this module" 2>/dev/null
```
