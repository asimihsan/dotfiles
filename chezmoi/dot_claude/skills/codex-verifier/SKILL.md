---
name: codex-verifier
description: Use OpenAI Codex CLI as a second-opinion agent for verification, exploration, and analysis tasks. Invoke when the user asks to verify assumptions, get a second opinion, cross-check analysis, explore alternatives, or use Codex for read-only analysis. Triggers on phrases like "verify with codex", "get a second opinion", "cross-check", "have codex analyze", "explore with codex".
---

# Codex Verifier

This skill enables Claude Code to delegate verification, analysis, and exploration tasks to OpenAI's Codex CLI as a second-opinion agent.

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
codex exec "Your prompt" 2>/dev/null

# WRONG - captures entire trajectory (all reasoning, file reads, commands)
codex exec --json "Your prompt"
```

## Core Use Cases

### 1. Verification / Second Opinion

Cross-check Claude's analysis or assumptions with an independent model:

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Verify this assumption: [ASSUMPTION]. Review the codebase and confirm or refute with evidence." 2>/dev/null
```

### 2. Exploration / Discovery

Explore unfamiliar code or patterns:

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Analyze the authentication flow in this codebase. Trace from login endpoint to session storage." 2>/dev/null
```

### 3. Architectural Analysis

Get independent architectural assessment:

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Review the architecture and identify potential bottlenecks or anti-patterns." 2>/dev/null
```

### 4. Test Coverage Validation

Verify test coverage assumptions:

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Analyze test coverage for the payment module. Identify untested edge cases." 2>/dev/null
```

## Command Patterns

### Basic Pattern (Recommended)

Always use ` for verification tasks and redirect stderr:

```bash
codex exec "PROMPT" 2>/dev/null
```

### Output to File

When you need to preserve the analysis for later reference:

```bash
codex exec -o /tmp/codex-analysis.md \
  "PROMPT" 2>/dev/null
cat /tmp/codex-analysis.md
```

### Specific Directory Analysis

Target a specific subdirectory:

```bash
codex exec -C ./src/auth \
  "Analyze security patterns in this module" 2>/dev/null
```

### Model Selection

Choose reasoning depth based on task complexity:

| Model | Use Case |
|-------|----------|
| `gpt-5.1-codex` | Fast analysis, simple verification |
| `gpt-5.1-codex-max` | Deep architectural analysis, complex verification |
| `gpt-5.2` | General reasoning tasks |

Default is `gpt-5.2` if `--model` is omitted.

## Verification Workflow

When asked to verify an assumption or get a second opinion:

1. **Formulate the verification prompt** - Be specific about what to verify
2. **Choose appropriate model** - Use `gpt-5.2` for most tasks, or `gpt-5.1-codex-max` for writing code.
3. **Use read-only mode** - Always ` for verification
4. **Redirect stderr** - Always `2>/dev/null` to avoid context bloat
5. **Synthesize results** - Compare Codex analysis with Claude's analysis
6. **Report discrepancies** - Highlight any differences in conclusions

## Example Verification Prompts

### Verify Code Correctness

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Review the function 'processPayment' in src/payments.ts. \
   Verify it handles: (1) network failures, (2) duplicate submissions, (3) partial failures. \
   Report any gaps." 2>/dev/null
```

### Verify Performance Assumptions

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Analyze the database query in src/queries/users.ts. \
   Is it O(n) or O(n^2)? Identify any N+1 query patterns." 2>/dev/null
```

### Verify Security Posture

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Security audit: Review authentication and authorization in this codebase. \
   Check for: SQL injection, XSS, CSRF, insecure defaults, hardcoded secrets." 2>/dev/null
```

### Verify Migration Safety

```bash
codex exec --full-auto --model gpt-5.2 -c reasoning.effort=xhigh --dangerously-bypass-approvals-and-sandbox \
  "Review the database migration in migrations/2025_add_index.sql. \
   Is it safe to run on a 10M row table in production? Estimate lock duration." 2>/dev/null
```

## Error Handling

If Codex CLI fails:

1. Check authentication: `codex login status`
2. Check network connectivity
3. Verify API quota/rate limits
4. Fall back to Claude-only analysis with explicit caveat

## When to Use This Skill

- User asks to "verify", "double-check", or "cross-check" something
- User wants a "second opinion" on analysis
- User asks to "have Codex/GPT-5 look at" something
- User wants to "explore" or "discover" patterns in unfamiliar code
- User asks for independent architectural review
- User wants to validate assumptions before making changes

## When NOT to Use This Skill

- Simple questions that do not benefit from verification
- Tasks requiring file modifications (use standard Codex skill instead)
- Real-time/interactive debugging sessions
- When user has not set up Codex CLI
