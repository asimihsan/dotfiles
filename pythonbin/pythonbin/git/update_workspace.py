#!/usr/bin/env python3

import concurrent
import enum
import multiprocessing
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import questionary
import rich
import rich.progress
from git import Repo, InvalidGitRepositoryError
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pydantic import BaseModel
from rich.console import Console

# Initialize the console for rich output
console = Console()


def add_untracked_to_gitignore(repo_path: Path, untracked_files: list[str]) -> None:
    common_exclude_patterns = {
        "python": ["**/.python-version", "**/__pycache__/", "**/*.pyc", ".python-version"],
        "terraform": ["**/.terraform/", "**/*.tfstate", "**/*.tfstate.backup"],
        "cdk": ["**/cdk.out/", "**/cdk.context.json"],
        "cdktf": ["**/.gen/", "**/cdktf.out/"],
        "java": ["**/*.class", "**/target/", "**/build/"],
        "javascript": ["**/node_modules/", "**/package-lock.json", "**/yarn.lock"],
        "intellij": ["**/.idea/", "**/*.iml"],
        "CACHEDIR.TAG": ["**/CACHEDIR.TAG"],
    }

    # Flatten the pattern list
    all_exclude_patterns = [pattern for patterns in common_exclude_patterns.values() for pattern in patterns]

    exclude_file_path = repo_path / ".git" / "info" / "exclude"
    patterns_used = set()
    with exclude_file_path.open("a") as exclude_file:
        for pattern in all_exclude_patterns:
            # Create a PathSpec for the current pattern
            spec = PathSpec.from_lines(GitWildMatchPattern, [pattern])

            # Check if the pattern matches any untracked file
            for file in untracked_files:
                if spec.match_file(file) and pattern not in patterns_used:
                    console.print(f"[yellow]Excluding pattern {pattern} for file {file}[/yellow]")
                    exclude_file.write(f"{pattern}\n")
                    patterns_used.add(pattern)
                    break  # Stop checking after the first match for this pattern

        # Add any remaining untracked files that did not match any pattern
        for file in untracked_files:
            if not any(
                PathSpec.from_lines(GitWildMatchPattern, [pattern]).match_file(file) for pattern in patterns_used
            ):
                console.print(f"[yellow]Excluding file {file}[/yellow]")
                exclude_file.write(f"{file}\n")


def is_git_repo(path):
    try:
        _ = Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False


def reset_submodules(repo_path):
    repo = Repo(repo_path)
    repo.git.submodule("update", "--init", "--recursive")
    repo.git.submodule("foreach", "--recursive", "git fetch --all")
    repo.git.submodule("foreach", "--recursive", "git reset --hard")
    repo.git.submodule("foreach", "--recursive", "git clean -fdx")


def handle_dirty_repo(repo_path):
    repo = Repo(repo_path)
    console.print(f"\n[yellow]Uncommitted changes in {repo_path}. Here's the status:[/yellow]")
    console.print(repo.git.status())

    choices: list[dict[str, str]] = [
        {"name": "Stash changes", "value": "s"},
        {"name": "Reset to HEAD (discard changes)", "value": "r"},
        {"name": "Continue without changes", "value": "c"},
        {"name": "Exclude untracked files", "value": "e"},
        {"name": "Abort and skip this repository", "value": "a"},
    ]
    action = questionary.select(
        "Choose an action:",
        choices=choices,
        default=choices[1],
    ).ask()

    if action == "s":
        repo.git.stash("save")
        return True
    elif action == "r":
        repo.git.reset("--hard")
        repo.git.clean("-fdx")
        reset_submodules(repo_path)  # Reset submodules
        console.print(f"[green]Reset to HEAD and cleaned untracked files in {repo_path}.[/green]")
        return True
    elif action == "c":
        return True
    elif action == "e":  # Logic for the new option
        untracked_files = repo.untracked_files
        add_untracked_to_gitignore(Path(repo_path), untracked_files)
        console.print(f"[green]Untracked files have been filtered and added to {repo_path}/.git/info/exclude[/green]")
        return True
    elif action == "a":
        return False
    else:
        console.print("[red]Invalid action. Skipping repository.[/red]")
        return False


def update_git_repo(repo_path, non_interactive: bool = False) -> bool:
    try:
        repo = Repo(repo_path)
        if repo.is_dirty(untracked_files=True):
            if non_interactive:
                return False
            if not handle_dirty_repo(repo_path):
                return False

        origin = repo.remotes.origin
        origin.pull(rebase=True)
        repo.submodule_update(recursive=True, init=True)  # Update submodules
        return True
    except Exception:
        return False


# Worker status enum
class WorkerStatus(enum.Enum):
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    EXIT = "exit"


class WorkerMessage(BaseModel):
    repo_path: str
    status: WorkerStatus


def update_git_repo_wrapper(repo_path, queue: multiprocessing.Queue) -> bool:
    queue.put(WorkerMessage(repo_path=repo_path, status=WorkerStatus.STARTED))
    try:
        result = update_git_repo(repo_path)
        if result:
            queue.put(WorkerMessage(repo_path=repo_path, status=WorkerStatus.SUCCESS))
        else:
            queue.put(WorkerMessage(repo_path=repo_path, status=WorkerStatus.FAILED))
        return result
    except Exception:
        queue.put(WorkerMessage(repo_path=repo_path, status=WorkerStatus.FAILED))
    return False


def progress_listener(queue: multiprocessing.Queue, idle: multiprocessing.Event) -> None:
    with rich.progress.Progress(
        rich.progress.SpinnerColumn(),
        rich.progress.TextColumn("[bold blue]{task.description}"),
        transient=True,
    ) as progress:
        tasks: dict[str, rich.progress.TaskID] = {}
        while True:
            if len(tasks) == 0:
                idle.set()
            else:
                idle.clear()

            message: WorkerMessage = queue.get()
            if message.status == WorkerStatus.STARTED:
                tasks[message.repo_path] = progress.add_task(message.repo_path, start=True)
            elif message.status == WorkerStatus.SUCCESS:
                task_id = tasks.pop(message.repo_path)
                progress.update(task_id, description=f"[green]{message.repo_path}")
                time.sleep(0.5)  # Briefly show success
                progress.remove_task(task_id)
            elif message.status == WorkerStatus.FAILED:
                task_id = tasks.pop(message.repo_path)
                progress.update(task_id, description=f"[red]{message.repo_path}")
                time.sleep(0.5)  # Briefly show failure
                progress.remove_task(task_id)
            elif message.status == "exit":  # Special exit message
                print("Exiting progress listener")
                break


def main() -> None:
    if len(sys.argv) != 2:
        console.print("[red]Usage: python update_repos.py <root_directory>[/red]")
        sys.exit(1)

    root_dir = sys.argv[1]

    if not os.path.isdir(root_dir):
        console.print(f"[red]Error: {root_dir} is not a directory.[/red]")
        sys.exit(1)

    subdirs = [os.path.join(root_dir, d) for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    random.shuffle(subdirs)
    git_dirs: set[str] = {d for d in subdirs if is_git_repo(d)}
    future_to_git_dir: dict[concurrent.futures.Future, str] = {}
    concurrent_limit: int = 4

    with multiprocessing.Manager() as manager, concurrent.futures.ProcessPoolExecutor(
        max_workers=concurrent_limit
    ) as executor:
        progress_queue = manager.Queue()
        progress_idle = multiprocessing.Event()
        progress_process = multiprocessing.Process(target=progress_listener, args=(progress_queue, progress_idle))
        progress_process.start()

        seen_errors: set[str] = set()
        try:
            while True:
                if seen_errors:
                    progress_idle.wait()
                    for git_dir in seen_errors:
                        if update_git_repo(git_dir, non_interactive=False):
                            git_dirs.add(git_dir)
                    seen_errors.clear()
                    continue

                if len(future_to_git_dir) == concurrent_limit:
                    done, _ = concurrent.futures.wait(future_to_git_dir, return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:
                        git_dir = future_to_git_dir.pop(future)
                        try:
                            result = future.result()
                            if not result:
                                seen_errors.add(git_dir)
                        except Exception:
                            seen_errors.add(git_dir)
                        if len(seen_errors) > 0:
                            break
                    continue

                if git_dirs:
                    git_dir = git_dirs.pop()
                    future = executor.submit(update_git_repo_wrapper, git_dir, progress_queue)
                    future_to_git_dir[future] = git_dir
                    continue

                if not future_to_git_dir and not seen_errors and not git_dirs:
                    break
        except KeyboardInterrupt:
            console.print("\n[red]CTRL-C detected. Waiting for current operations to finish...[/red]")
            progress_queue.put(WorkerMessage(repo_path="", status="exit"))
            progress_process.join()
            console.print("[bold red]Script aborted.[/bold red]")
            sys.exit(1)

    print("Waiting for progress listener to exit")
    progress_queue.put(WorkerMessage(repo_path="", status="exit"))
    progress_process.join()

    console.print("[bold green]Script completed successfully[/bold green]")
