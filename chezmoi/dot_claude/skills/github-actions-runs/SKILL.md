---
name: github-actions-runs
description: Automate and inspect GitHub Actions runs with the asim-utilities Python library/CLI. Use when triggering workflows, listing recent runs or failures, waiting/canceling runs on job failure, or downloading run logs and artifacts. Covers CLI usage, output conventions, and repo layout for ~/workplace/asim-utilities.
---

# GitHub Actions Runs

## Overview
Use the `asim-utilities` repo to manage GitHub Actions runs via a typed Python library and the `gh-actions-runs` CLI. This skill covers common workflows (trigger/watch, list failures, download logs/artifacts), configuration, and where to modify the code.

## Quick start (CLI)
- Set auth: `GITHUB_TOKEN` or `GH_TOKEN` in the environment.
- Run against current repo (auto-detects `origin`), or pass `--repo owner/name`.
- Default output root: `~/.cache/gh-actions-runs` (override with `--output`).

Common commands:
- Trigger + wait for run ID:
  - `gh-actions-runs trigger --workflow CI --ref main --wait`
- Watch a run, cancel on first failure, download logs/artifacts:
  - `gh-actions-runs watch --workflow CI --ref main`
- List recent runs:
  - `gh-actions-runs list --limit 20`
- List recent failures:
  - `gh-actions-runs failures --limit 10`
- Download logs + artifacts for a run:
  - `gh-actions-runs download 123456`

## Workflow: Trigger + watch
1. Dispatch workflow (`trigger` or `watch` without `--run-id`).
2. Poll for the run ID based on creation time + branch.
3. Poll run + jobs; if any job fails and `--no-cancel-on-failure` is not set, cancel the run.
4. Wait for completion, then download logs and artifacts into `run-<id>/`.

## Workflow: Inspect recent runs
- Use `list` for recent runs; add `--workflow` or `--branch` filters.
- Use `failures` to filter for failed conclusions.
- Use `run` and `jobs` to inspect a single run in detail.

## Output and formats
- `--format human` (default): tables and readable summaries.
- `--format json`: machine-readable output for scripting.

## Code map
- Library: `src/asim_utilities/github_actions/`
  - `client.py`: GitHub REST API client
  - `runs.py`: high-level run operations
  - `models.py`: typed dataclasses
  - `utils.py`: helpers (token, repo parsing, XDG cache paths)
- CLI: `src/asim_utilities/github_actions/cli.py`

## Installation notes
- `gh-actions-runs` entry point is installed via editable install and linked into `~/bin`.
- If a rebuild is needed, rerun the repo install steps (see repo setup).
