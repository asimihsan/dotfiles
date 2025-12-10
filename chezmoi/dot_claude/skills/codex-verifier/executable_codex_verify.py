#!/usr/bin/env python3
"""
codex_verify.py - Run Codex CLI in verification mode and parse results.

Usage:
    python codex_verify.py "Verify the authentication flow handles token expiry"
    python codex_verify.py --model gpt-5.1-codex-max "Deep security audit"
    python codex_verify.py --dir ./src/auth "Analyze this module"
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_codex_verification(
    prompt: str,
    model: str = "gpt-5.1-codex",
    directory: str | None = None,
    timeout: int = 300,
) -> dict:
    """
    Run Codex CLI in read-only mode and return parsed results.
    
    Returns:
        dict with keys: success, messages, commands, errors, raw_events
    """
    cmd = [
        "codex", "exec",
        "-s", "read-only",
        "--json",
        "-m", model,
        prompt
    ]
    
    if directory:
        cmd.extend(["-C", directory])
    
    result = {
        "success": False,
        "messages": [],
        "commands": [],
        "file_reads": [],
        "errors": [],
        "raw_events": [],
    }
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        # Parse JSONL output (each line is a JSON event)
        for line in proc.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                event = json.loads(line)
                result["raw_events"].append(event)
                
                event_type = event.get("type", "")
                
                if event_type == "message":
                    result["messages"].append(event.get("content", ""))
                elif event_type == "command":
                    result["commands"].append({
                        "command": event.get("command", ""),
                        "output": event.get("output", ""),
                    })
                elif event_type == "file_read":
                    result["file_reads"].append(event.get("path", ""))
                elif event_type == "error":
                    result["errors"].append(event.get("message", ""))
                    
            except json.JSONDecodeError:
                # Non-JSON output, might be progress indicator
                pass
        
        # Also capture stderr for any errors
        if proc.stderr:
            result["errors"].append(proc.stderr)
        
        result["success"] = proc.returncode == 0 and len(result["errors"]) == 0
        
    except subprocess.TimeoutExpired:
        result["errors"].append(f"Codex timed out after {timeout}s")
    except FileNotFoundError:
        result["errors"].append("Codex CLI not found. Install with: npm i -g @openai/codex")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")
    
    return result


def format_verification_report(result: dict) -> str:
    """Format the verification result as a readable report."""
    lines = []
    
    if result["success"]:
        lines.append("## Codex Verification: SUCCESS\n")
    else:
        lines.append("## Codex Verification: ISSUES FOUND\n")
        if result["errors"]:
            lines.append("### Errors")
            for err in result["errors"]:
                lines.append(f"- {err}")
            lines.append("")
    
    if result["messages"]:
        lines.append("### Analysis")
        # Get the final/most complete message
        final_message = result["messages"][-1] if result["messages"] else ""
        lines.append(final_message)
        lines.append("")
    
    if result["file_reads"]:
        lines.append("### Files Examined")
        for f in result["file_reads"][:20]:  # Limit to 20
            lines.append(f"- {f}")
        if len(result["file_reads"]) > 20:
            lines.append(f"- ... and {len(result["file_reads"]) - 20} more")
        lines.append("")
    
    if result["commands"]:
        lines.append("### Commands Executed")
        for cmd in result["commands"][:10]:
            lines.append(f"```\n{cmd['command']}\n```")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Run Codex CLI verification and parse results"
    )
    parser.add_argument("prompt", help="Verification prompt for Codex")
    parser.add_argument(
        "--model", "-m",
        default="gpt-5.1-codex",
        help="Model to use (default: gpt-5.1-codex)"
    )
    parser.add_argument(
        "--dir", "-C",
        help="Directory to analyze"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted report"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write output to file"
    )
    
    args = parser.parse_args()
    
    result = run_codex_verification(
        prompt=args.prompt,
        model=args.model,
        directory=args.dir,
        timeout=args.timeout,
    )
    
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_verification_report(result)
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}")
    else:
        print(output)
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
