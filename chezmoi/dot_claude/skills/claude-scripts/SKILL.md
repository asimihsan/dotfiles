---
name: claude-scripts
description: CLI to search Claude Code conversation history by tool, pattern, or time, and export results.
---

# claude-scripts

Search conversation history stored in `~/.claude/projects/`.

## Quick Start

```bash
claude-scripts search --tool Bash
claude-scripts search --type thinking --pattern "architecture"
claude-scripts search --tool "mcp__*" --summary
claude-scripts search --pattern "deploy" --format json
```

## Key Flags

- `--type/-t`: `thinking`, `text`, `tool_use`, `tool_result`
- `--tool/-T`: filter tool names; supports wildcards (`"mcp__*"`)
- `--pattern/-P`: substring; add `--regex` or `--case-sensitive`
- `--after/--before`: time range (`YYYY-MM-DD` or ISO datetime)
- `--format/-F`: `text` (default), `table`, `json`, `jsonl`
- `--short-path`: abbreviate file paths (full paths shown by default)
- `-C/--context N`: N entries before/after each match (text format only)
- `--summary`: show match counts per conversation instead of individual results

## Common Workflows

```bash
# Yesterday's tool usage
claude-scripts search --type tool_use --after "2025-12-10" --format table

# All git Bash commands
claude-scripts search --tool Bash --pattern "git "

# Export one project to JSON
claude-scripts search --project myproject --format json > conv.json

# Search specific conversation file
claude-scripts search --file ~/.claude/projects/-Users-me-project/session.jsonl --tool Read

# Audit MCP tool usage
claude-scripts search --tool "mcp__*" --summary
```
