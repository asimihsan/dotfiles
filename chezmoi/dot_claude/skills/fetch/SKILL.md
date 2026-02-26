---
name: fetch
description: Fetch web content with a Python helper that supports query args, headers, chunked output, and HTML simplification to Markdown. Use when Claude needs to retrieve and inspect URL content, including work-host TLS interception where only hostname `okzf68` should trust `~/.config/certs/node-extra-ca.pem`.
---

# Fetch

## Overview
Use this skill to fetch HTTP(S) URLs through `scripts/fetch_url.py` and return structured JSON with chunked content for LLM workflows.

## Run Workflow
1. Run the script with `uv run --project . python scripts/fetch_url.py --url <URL>` from this skill directory.
2. Pass query args with repeated `--query key=value` and request headers with repeated `--header 'Name: Value'`.
3. Keep HTML simplification enabled by default; use `--raw` to skip simplification.
4. Page large outputs with `--start-index` and `--max-chars`.
5. Check TLS diagnostics in output:
   - `tls_extra_ca_configured`
   - `tls_extra_ca_loaded`
   - `tls_extra_ca_path`
6. From source repo checkout, run `scripts/validate_fetch_skill.sh` to validate template rendering, syntax, and TLS diagnostics for work/home variants.

## TLS Interception Behavior
- Keep host-specific CA configuration in `scripts/fetch_url.py.tmpl`.
- Render `EXTRA_CA_CERT` only on `okzf68`:
  - `"{{ .chezmoi.homeDir }}/.config/certs/node-extra-ca.pem"`
- Render `EXTRA_CA_CERT = None` on other hosts.
- Do not disable TLS verification.

## Examples

```bash
# Basic fetch with HTML simplification
uv run --project . python scripts/fetch_url.py \
  --url https://example.com

# Fetch with query args and custom header
uv run --project . python scripts/fetch_url.py \
  --url https://httpbin.org/get \
  --query q=search-term \
  --query page=1 \
  --header 'Accept: text/html'

# Fetch a later chunk of content
uv run --project . python scripts/fetch_url.py \
  --url https://example.com \
  --start-index 5000 \
  --max-chars 3000

# Skip HTML simplification and keep raw text
uv run --project . python scripts/fetch_url.py \
  --url https://example.com \
  --raw
```

## Resources
- Use `references/mcp-reuse-decisions.md` for MCP fetch reuse rationale and source links.
