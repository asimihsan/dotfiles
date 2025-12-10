---
name: codex-verifier
description: Use OpenAI Codex CLI as a second-opinion agent for verification, exploration, and analysis tasks. Invoke when the user asks to verify assumptions, get a second opinion, cross-check analysis, explore alternatives, or use Codex/GPT-5 for read-only analysis. Triggers on phrases like "verify with codex", "get a second opinion", "cross-check", "have codex analyze", "explore with gpt-5".
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

## Core Use Cases

### 1. Verification / Second Opinion

Cross-check Claude's analysis or assumptions with an independent model:

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Verify this assumption: [ASSUMPTION]. Review the codebase and confirm or refute with evidence."
```

### 2. Exploration / Discovery

Explore unfamiliar code or patterns:

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Analyze the authentication flow in this codebase. Trace from login endpoint to session storage."
```

### 3. Architectural Analysis

Get independent architectural assessment:

```bash
codex exec -s read-only --json --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Review the architecture and identify potential bottlenecks or anti-patterns." \
  | jq '.[] | select(.type == "message") | .content'
```

### 4. Test Coverage Validation

Verify test coverage assumptions:

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Analyze test coverage for the payment module. Identify untested edge cases."
```

## Command Patterns

### Read-Only Analysis (Default for Verification)

Always use `-s read-only` for verification tasks to prevent mutations:

```bash
codex exec -s read-only "PROMPT"
```

### JSON Output for Parsing

When you need structured output for further processing:

```bash
codex exec -s read-only --json "PROMPT" 2>/dev/null | \
  jq -r '.[] | select(.type == "message") | .content'
```

### Output to File for Review

Save analysis for comparison:

```bash
codex exec -s read-only -o /tmp/codex-analysis.md "PROMPT"
```

### Specific Directory Analysis

Target a specific subdirectory:

```bash
codex exec -s read-only -C ./src/auth "Analyze security patterns in this module"
```

### Model Selection

Choose reasoning depth based on task complexity:

| Model | Use Case |
|-------|----------|
| `gpt-5.1-codex` | Fast analysis, simple verification |
| `gpt-5.1-codex-max` | Deep architectural analysis, complex verification |
| `gpt-5` | General reasoning tasks |

## Verification Workflow

When asked to verify an assumption or get a second opinion:

1. **Formulate the verification prompt** - Be specific about what to verify
2. **Choose appropriate model** - Use `gpt-5.1-codex` for most tasks
3. **Use read-only mode** - Always `-s read-only` for verification
4. **Capture output** - Use `--json` or `-o` for structured capture
5. **Synthesize results** - Compare Codex analysis with Claude's analysis
6. **Report discrepancies** - Highlight any differences in conclusions

## Example Verification Prompts

### Verify Code Correctness

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Review the function 'processPayment' in src/payments.ts. \
   Verify it handles: (1) network failures, (2) duplicate submissions, (3) partial failures. \
   Report any gaps."
```

### Verify Performance Assumptions

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Analyze the database query in src/queries/users.ts. \
   Is it O(n) or O(n^2)? Identify any N+1 query patterns."
```

### Verify Security Posture

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox-max \
  "Security audit: Review authentication and authorization in this codebase. \
   Check for: SQL injection, XSS, CSRF, insecure defaults, hardcoded secrets."
```

### Verify Migration Safety

```bash
codex exec -s read-only --model gpt-5.1-codex-max --dangerously-bypass-approvals-and-sandbox \
  "Review the database migration in migrations/2025_add_index.sql. \
   Is it safe to run on a 10M row table in production? Estimate lock duration."
```

## Output Processing

### Extract Final Message Only

```bash
OUTPUT=$(codex exec -s read-only --json "PROMPT" 2>/dev/null)
FINAL=$(echo "$OUTPUT" | jq -r '[.[] | select(.type == "message")] | last | .content')
echo "$FINAL"
```

### Compare Two Analyses

```bash
# Get Claude's analysis (already in context)
# Get Codex's analysis
codex exec -s read-only -o /tmp/codex-view.md "Analyze the auth module"
# Now compare both in Claude's response
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
