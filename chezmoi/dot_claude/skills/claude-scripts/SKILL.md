---
name: claude-scripts
description: Search and analyze Claude Code conversation history using the claude-scripts CLI. Use when: (1) Finding specific tool invocations (Bash, Read, mcp__* tools), (2) Searching conversation content by pattern or regex, (3) Extracting thinking blocks or text responses, (4) Filtering conversations by time range, (5) Analyzing which tools were used in past sessions, (6) Exporting conversation data as JSON.
---

# claude-scripts

Search Claude Code conversation history stored in `~/.claude/projects/`.

## Quick Start

```bash
# Search for Bash commands
claude-scripts search --tool Bash

# Find thinking blocks mentioning "architecture"
claude-scripts search --type thinking --pattern "architecture"

# List all MCP tool invocations
claude-scripts search --tool "mcp__*"

# Export as JSON
claude-scripts search --tool Read --format json
```

## Search Options

### Content Type (`--type` / `-t`)
Filter by what Claude produced:
- `thinking` - Internal reasoning blocks
- `text` - Text responses
- `tool_use` - Tool invocations
- `tool_result` - Tool outputs

### Tool Name (`--tool` / `-T`)
Filter tool invocations by name. Supports wildcards:
```bash
--tool Bash              # Exact match
--tool "mcp__*"          # All MCP tools
--tool "mcp__github__*"  # GitHub MCP tools
```

### Pattern (`--pattern` / `-P`)
Text search with optional regex:
```bash
--pattern "deploy"           # Substring match
--pattern "error.*timeout" --regex  # Regex
--pattern "AWS" --case-sensitive    # Case-sensitive
```

### Time Range (`--after` / `--before`)
```bash
--after "2025-12-01"
--before "2025-12-05"
--after "2025-12-01T10:00:00"
```

### Output (`--format` / `-F`)
- `text` (default) - Human-readable
- `table` - Columnar format
- `json` - JSON array
- `jsonl` - Line-delimited JSON

### Full Path (`--full-path`)
Show complete file paths without abbreviation:
```bash
claude-scripts search --pattern "error" --full-path
```

### Context Lines (`-C` / `--context`)
Show N entries before and after each match (like grep -C):
```bash
claude-scripts search --pattern "deploy" -C 2      # 2 entries before/after
claude-scripts search --tool Bash --pattern "git" -C 1
```

Note: Context mode only works with `--format text` and requires `--pattern` or `--tool`.

### Summary Mode (`--summary`)
Show which conversations have matches and counts instead of individual results:
```bash
claude-scripts search --pattern "error" --summary
claude-scripts search --tool Bash --summary --format json
```

## Common Workflows

```bash
# What tools did I use yesterday?
claude-scripts search --type tool_use --after "2025-12-04" --format table

# Find all git commands
claude-scripts search --tool Bash --pattern "git "

# Export conversation to JSON for analysis
claude-scripts search --project myproject --format json > conv.json

# Search specific conversation file
claude-scripts search --file ~/.claude/projects/-Users-me-project/session.jsonl --tool Read

# Find which conversations discussed a PR
claude-scripts search --pattern "PR-1234" --summary

# See context around errors
claude-scripts search --pattern "error" --type tool_result -C 2

# Full audit of MCP tool usage with file paths
claude-scripts search --tool "mcp__*" --full-path --summary
```
