#!/usr/bin/env python3
"""Bootstrap backlog + AGENTS + mise + jujutsu repo conventions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


BOOTSTRAP_HEADER = "## Repo Bootstrap Standards"
BACKLOG_HEADER = "## Backlog plans and tasks"
BOOTSTRAP_SENTINEL = "Use plan tool to track tasks."
BACKLOG_SENTINEL = "Plans should use the template in `backlog/plans/_template.md`."


@dataclass
class Action:
    status: str
    path: Path
    detail: str


def emit(actions: list[Action], status: str, path: Path, detail: str) -> None:
    action = Action(status=status, path=path, detail=detail)
    actions.append(action)
    print(f"[{status}] {path}: {detail}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_dir(path: Path, dry_run: bool, actions: list[Action]) -> None:
    if path.exists():
        emit(actions, "ok", path, "directory already exists")
        return
    if dry_run:
        emit(actions, "plan", path, "create directory")
        return
    path.mkdir(parents=True, exist_ok=True)
    emit(actions, "write", path, "created directory")


def write_content(
    target: Path,
    content: str,
    force: bool,
    dry_run: bool,
    actions: list[Action],
    label: str,
) -> bool:
    existed = target.exists()
    if existed:
        existing = read_text(target)
        if existing == content:
            emit(actions, "ok", target, f"already up to date ({label})")
            return False
        if not force:
            emit(actions, "skip", target, f"exists; pass --force to overwrite ({label})")
            return False

    if dry_run:
        verb = "overwrite" if existed else "create"
        emit(actions, "plan", target, f"{verb} file ({label})")
        return True

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    verb = "overwrote" if existed else "created"
    emit(actions, "write", target, f"{verb} file ({label})")
    return True


def copy_template(
    templates_root: Path,
    template_relative: str,
    repo: Path,
    target_relative: str,
    force: bool,
    dry_run: bool,
    actions: list[Action],
) -> bool:
    template_path = templates_root / template_relative
    target_path = repo / target_relative
    content = read_text(template_path)
    return write_content(
        target=target_path,
        content=content,
        force=force,
        dry_run=dry_run,
        actions=actions,
        label=template_relative,
    )


def mark_executable(path: Path, dry_run: bool, actions: list[Action]) -> None:
    if dry_run:
        emit(actions, "plan", path, "mark executable")
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)
    emit(actions, "write", path, "marked executable")


def ensure_backlog_excluded(repo: Path, dry_run: bool, actions: list[Action]) -> None:
    git_dir = repo / ".git"
    exclude_path = git_dir / "info" / "exclude"

    if not git_dir.exists():
        emit(actions, "skip", exclude_path, ".git not found; skipped exclude update")
        return

    existing = read_text(exclude_path) if exclude_path.exists() else ""
    lines = existing.splitlines()
    if "backlog/" in lines:
        emit(actions, "ok", exclude_path, "`backlog/` already excluded")
        return

    updated = existing
    if updated and not updated.endswith("\n"):
        updated += "\n"
    updated += "backlog/\n"

    if dry_run:
        emit(actions, "plan", exclude_path, "append `backlog/` to git exclude")
        return

    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    exclude_path.write_text(updated, encoding="utf-8")
    emit(actions, "write", exclude_path, "added `backlog/` to git exclude")


def normalize_goal(goal: str) -> str:
    normalized = " ".join(goal.split())
    if not normalized:
        normalized = "replace with repository goal"
    if not normalized.endswith("."):
        normalized += "."
    return normalized


def update_agents(
    repo: Path,
    templates_root: Path,
    agents_mode: str,
    project_goal: str,
    force: bool,
    dry_run: bool,
    actions: list[Action],
) -> None:
    agents_path = repo / "AGENTS.md"
    full_template = read_text(templates_root / "AGENTS.new.md")
    bootstrap_section = read_text(templates_root / "AGENTS.bootstrap-section.md").strip()
    backlog_section = read_text(templates_root / "AGENTS.backlog-section.md").strip()

    if agents_mode == "skip":
        emit(actions, "skip", agents_path, "AGENTS update skipped (--agents-mode skip)")
        return

    # Missing AGENTS in auto/merge mode falls back to full template creation.
    if not agents_path.exists() and agents_mode in {"auto", "merge"}:
        rendered = full_template.replace("{{PROJECT_GOAL}}", normalize_goal(project_goal))
        write_content(
            target=agents_path,
            content=rendered,
            force=False,
            dry_run=dry_run,
            actions=actions,
            label="AGENTS.new.md",
        )
        return

    if agents_mode == "overwrite":
        rendered = full_template.replace("{{PROJECT_GOAL}}", normalize_goal(project_goal))
        write_content(
            target=agents_path,
            content=rendered,
            force=True,
            dry_run=dry_run,
            actions=actions,
            label="AGENTS.new.md (overwrite)",
        )
        return

    # Merge mode for existing AGENTS.
    existing = read_text(agents_path)
    changed = False
    merged = existing.rstrip() + "\n"

    has_bootstrap = BOOTSTRAP_HEADER in existing or BOOTSTRAP_SENTINEL in existing
    if not has_bootstrap:
        # Add the full standard section only when the section is missing.
        merged += "\n" + bootstrap_section + "\n"
        changed = True

    has_backlog = BACKLOG_HEADER in existing or BACKLOG_SENTINEL in existing
    if not has_backlog:
        merged += "\n" + backlog_section + "\n"
        changed = True

    if not changed:
        emit(actions, "ok", agents_path, "already contains backlog + bootstrap sections")
        return

    write_content(
        target=agents_path,
        content=merged,
        force=True,
        dry_run=dry_run,
        actions=actions,
        label="merged AGENTS sections",
    )


def ensure_mise_defaults(
    repo: Path,
    templates_root: Path,
    force: bool,
    dry_run: bool,
    actions: list[Action],
) -> None:
    targets = [
        ("mise.toml", "mise.toml"),
        ("tasks.core.toml", "tasks.core.toml"),
        ("scripts/env.sh", "scripts/env.sh"),
        ("scripts/postinstall.sh", "scripts/postinstall.sh"),
    ]

    for template_relative, target_relative in targets:
        changed = copy_template(
            templates_root=templates_root,
            template_relative=template_relative,
            repo=repo,
            target_relative=target_relative,
            force=force,
            dry_run=dry_run,
            actions=actions,
        )
        if changed and target_relative.endswith(".sh"):
            mark_executable(repo / target_relative, dry_run=dry_run, actions=actions)


def ensure_jujutsu(
    repo: Path,
    init_jj: bool,
    dry_run: bool,
    actions: list[Action],
) -> None:
    jj_dir = repo / ".jj"
    git_dir = repo / ".git"

    if jj_dir.exists():
        emit(actions, "ok", jj_dir, "jujutsu workspace already initialized")
        return

    if not init_jj:
        if git_dir.exists():
            emit(actions, "note", jj_dir, "missing; run `jj git init --colocate` when ready")
        else:
            emit(
                actions,
                "note",
                jj_dir,
                "missing and .git not found; initialize git, then run `jj git init --colocate`",
            )
        return

    if not git_dir.exists():
        emit(actions, "skip", jj_dir, "--init-jj requested but .git not found")
        return

    cmd = ["jj", "git", "init", "--colocate"]
    if dry_run:
        emit(actions, "plan", jj_dir, f"run: {' '.join(cmd)} (cwd={repo})")
        return

    try:
        subprocess.run(
            cmd,
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`jj` command not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "").strip()
        tail = output.splitlines()[-1] if output else "no output"
        raise RuntimeError(f"failed to run `{' '.join(cmd)}`: {tail}") from exc

    emit(actions, "write", jj_dir, "initialized jujutsu with `jj git init --colocate`")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--agents-mode",
        default="auto",
        choices=["auto", "overwrite", "merge", "skip"],
        help="How to update AGENTS.md (default: auto).",
    )
    parser.add_argument(
        "--project-goal",
        default="an easy to use, easy to maintain project with reproducible local workflows",
        help="Goal sentence used when writing AGENTS.md from template.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when template content differs.",
    )
    parser.add_argument(
        "--skip-mise",
        action="store_true",
        help="Skip mise.toml/task script bootstrap.",
    )
    parser.add_argument(
        "--init-jj",
        action="store_true",
        help="Initialize jujutsu automatically (`jj git init --colocate`) when needed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes only.",
    )
    return parser.parse_args()


def summarize(actions: list[Action]) -> None:
    counts: dict[str, int] = {}
    for action in actions:
        counts[action.status] = counts.get(action.status, 0) + 1
    ordered = ["write", "plan", "ok", "skip", "note"]
    summary = ", ".join(f"{status}={counts[status]}" for status in ordered if status in counts)
    print(f"\nSummary: {summary if summary else 'no actions'}")


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"error: repo path is not a directory: {repo}", file=sys.stderr)
        return 1

    skill_root = Path(__file__).resolve().parents[1]
    templates_root = skill_root / "assets" / "templates"
    if not templates_root.exists():
        print(f"error: templates directory not found: {templates_root}", file=sys.stderr)
        return 1

    actions: list[Action] = []
    try:
        backlog_dirs = [
            repo / "backlog",
            repo / "backlog" / "docs",
            repo / "backlog" / "plans",
            repo / "backlog" / "tasks",
            repo / "backlog" / "tasks" / "completed",
        ]
        for path in backlog_dirs:
            ensure_dir(path=path, dry_run=args.dry_run, actions=actions)

        copy_template(
            templates_root=templates_root,
            template_relative="backlog/plans/_template.md",
            repo=repo,
            target_relative="backlog/plans/_template.md",
            force=args.force,
            dry_run=args.dry_run,
            actions=actions,
        )
        copy_template(
            templates_root=templates_root,
            template_relative="backlog/tasks/_template.md",
            repo=repo,
            target_relative="backlog/tasks/_template.md",
            force=args.force,
            dry_run=args.dry_run,
            actions=actions,
        )
        copy_template(
            templates_root=templates_root,
            template_relative="backlog/docs/README.md",
            repo=repo,
            target_relative="backlog/docs/README.md",
            force=args.force,
            dry_run=args.dry_run,
            actions=actions,
        )
        ensure_backlog_excluded(repo=repo, dry_run=args.dry_run, actions=actions)

        update_agents(
            repo=repo,
            templates_root=templates_root,
            agents_mode=args.agents_mode,
            project_goal=args.project_goal,
            force=args.force,
            dry_run=args.dry_run,
            actions=actions,
        )

        if args.skip_mise:
            emit(actions, "skip", repo / "mise.toml", "skipped mise bootstrap (--skip-mise)")
        else:
            ensure_mise_defaults(
                repo=repo,
                templates_root=templates_root,
                force=args.force,
                dry_run=args.dry_run,
                actions=actions,
            )

        ensure_jujutsu(
            repo=repo,
            init_jj=args.init_jj,
            dry_run=args.dry_run,
            actions=actions,
        )

    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)
        summarize(actions)
        return 1

    summarize(actions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
