import json
import sys
import subprocess
import os
from typing import List, Optional
import linecache
import tempfile
from dataclasses import dataclass
import argparse

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput


@dataclass
class Position:
    Filename: str
    Offset: int
    Line: int
    Column: int


@dataclass
class LintIssue:
    FromLinter: str
    Text: str
    Severity: str
    SourceLines: List[str]
    Replacement: Optional[str]
    Pos: Position
    ExpectNoLint: bool
    ExpectedNoLintLinter: str

    @classmethod
    def from_dict(cls, data):
        # Convert the 'Pos' dict to a Position object
        data["Pos"] = Position(**data["Pos"])
        return cls(**data)


def setup_aider(old_coder: Coder | None = None) -> Coder:
    model = Model("anthropic/claude-3-5-sonnet-20240620")
    io = InputOutput(yes=True)  # This sets up aider to automatically say yes to prompts
    return Coder.create(main_model=model, io=io, from_coder=old_coder, auto_commits=False)


def run_golangci_lint(working_dir: str, lint_command: str) -> List[LintIssue]:
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        cmd = lint_command.format(temp_file.name)
        print(f"Running golangci-lint with command: {cmd}")

        try:
            # Run the command and redirect output to the temporary file
            subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=temp_file,
                stderr=subprocess.PIPE,
                cwd=working_dir,
            )

            # Read the content of the temporary file
            temp_file.seek(0)
            lint_output = temp_file.read()

            # Parse the JSON output
            lint_results = json.loads(lint_output)
            return [
                LintIssue.from_dict(issue) for issue in lint_results.get("Issues", [])
            ]
        except subprocess.CalledProcessError as e:
            print(f"Error running golangci-lint: {e}")
            print(e.stderr.decode())
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing golangci-lint output: {e}")
            sys.exit(1)


def get_line_context(file_path: str, line_number: int, context_lines: int = 3) -> str:
    context = []
    start = max(1, line_number - context_lines)
    end = line_number + context_lines + 1

    for i in range(start, end):
        line = linecache.getline(file_path, i).rstrip()
        if not line and i > line_number:
            break  # Stop if we've gone past the end of the file
        prefix = "> " if i == line_number else "  "
        context.append(f"{prefix}{i}: {line}")

    return "\n".join(context)

def prepare_batch(lint_results: list[LintIssue], batch_size: int) -> list[list[LintIssue]]:
    batches = []
    current_batch = []
    added_files = set()

    for issue in lint_results:
        if issue.Pos.Filename not in added_files:
            added_files.add(issue.Pos.Filename)
            current_batch.append(issue)

        if len(current_batch) == batch_size:
            batches.append(current_batch)
            current_batch = []
            added_files.clear()

    if current_batch:
        batches.append(current_batch)

    return batches


def fix_lint_issues(coder: Coder, issues: list[LintIssue], working_dir: str):
    # Display all issues in the batch
    print("\nIssues to be fixed in this batch:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue.Pos.Filename}:{issue.Pos.Line} - {issue.FromLinter}: {issue.Text}")

    # Ask for user confirmation
    user_input = input("\nPress Enter to fix these issues, or 'q' to quit: ")
    if user_input.lower() == 'q':
        return

    # Add all relevant files to coder
    unique_files = set(issue.Pos.Filename for issue in issues)
    for filename in unique_files:
        coder.add_rel_fname(filename)

    # Create a combined prompt for all issues
    prompt = "Fix the following issues:\n"
    for issue in issues:
        full_path = os.path.join(working_dir, issue.Pos.Filename)
        prompt += f"- In {full_path} at line {issue.Pos.Line}: {issue.FromLinter} - {issue.Text}\n"
        prompt += f"  Context:\n{get_line_context(full_path, issue.Pos.Line)}\n"

    # Use coder to fix all issues
    coder.run(prompt)

    # Remove files from coder
    for filename in unique_files:
        coder.drop_rel_fname(filename)

    # Show context after fixes
    print("\nAfter fixes:")
    for issue in issues:
        full_path = os.path.join(working_dir, issue.Pos.Filename)
        print(f"Issue in {issue.Pos.Filename} at line {issue.Pos.Line}:")
        print(get_line_context(full_path, issue.Pos.Line))
        print()

    # Clear linecache after processing all files
    linecache.clearcache()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Lint fixer using aider and golangci-lint"
    )
    parser.add_argument(
        "--working-dir", type=str, default=".", help="Working directory for the project"
    )
    parser.add_argument(
        "--lint-command",
        type=str,
        default="make envfile && source external-build.env && make generate-mocks && golangci-lint run ./... --concurrency 8 --issues-exit-code 0 --out-format=json > {}",
        help="Command to run golangci-lint",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of lint issues to fix in each batch (default: 5)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    working_dir = os.path.abspath(args.working_dir)

    if not os.path.isdir(working_dir):
        print(f"Error: {working_dir} is not a valid directory")
        sys.exit(1)

    lint_results: list[LintIssue] = run_golangci_lint(working_dir, args.lint_command)
    lint_batches: list[list[LintIssue]] = prepare_batch(lint_results, args.batch_size)

    os.chdir(working_dir)

    coder: Coder | None = None

    for issues in lint_batches:
        coder = setup_aider(coder)
        fix_lint_issues(coder, issues, working_dir)


if __name__ == "__main__":
    main()
