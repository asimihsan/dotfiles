# MCP Reuse Decisions

## Sources
- `https://github.com/modelcontextprotocol/servers`
- `https://raw.githubusercontent.com/modelcontextprotocol/servers/refs/heads/main/src/fetch/src/mcp_server_fetch/server.py`
- `https://raw.githubusercontent.com/modelcontextprotocol/servers/refs/heads/main/src/fetch/src/mcp_server_fetch/__init__.py`
- `https://pypi.org/project/mcp-server-fetch/`
- Local research notes: `/private/tmp/foo.txt`

## Adopted Patterns
- Keep chunked output semantics with `start_index` + max-length style paging to make repeated fetches LLM-friendly.
- Keep HTML simplification pipeline (Readability-style extraction, then Markdown conversion).
- Keep optional proxy support to allow enterprise network compatibility.
- Keep simple, single-purpose fetch behavior and JSON output for deterministic downstream parsing.

## Rejected Patterns
- Reject direct code copy from MCP fetch server.
  - Reason: this skill needs host-specific TLS interception behavior and local chezmoi templating.
- Reject default TLS behavior without explicit custom CA support.
  - Reason: work host requires loading `~/.config/certs/node-extra-ca.pem` only on hostname `okzf68`.
- Reject unbounded response-body reads.
  - Reason: this can cause unnecessary memory growth during large fetches.
- Reject relying only on MCP defaults for safety guardrails.
  - Reason: this skill explicitly validates URL scheme and enforces deterministic byte/character limits.
