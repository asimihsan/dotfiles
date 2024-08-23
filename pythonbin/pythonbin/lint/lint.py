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


def fix_lint_issue(coder: Coder, issue: LintIssue, working_dir: str):
    full_path = os.path.join(working_dir, issue.Pos.Filename)
    print(f"\nIssue in {full_path} at line {issue.Pos.Line}:")
    print(f"Linter: {issue.FromLinter}")
    print(f"Message: {issue.Text}")
    print("\nContext:")
    print(get_line_context(full_path, issue.Pos.Line))

    user_input = input(
        "Press Enter to continue fixing this issue, or 'q' to quit: "
    )
    if user_input.lower() == "q":
        sys.exit(0)

    # Use aider to fix the issue
    coder.add_rel_fname(issue.Pos.Filename)
    coder.run(
        f"Fix the following {issue.FromLinter} issue in {full_path} at line {issue.Pos.Line}: {issue.Text}"
    )
    coder.drop_rel_fname(issue.Pos.Filename)

    print("\nAfter fix:")
    print(get_line_context(full_path, issue.Pos.Line))

    linecache.clearcache()  # Clear the cache to ensure we read the updated file


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
    return parser.parse_args()


def main():
    args = parse_arguments()
    working_dir = os.path.abspath(args.working_dir)

    if not os.path.isdir(working_dir):
        print(f"Error: {working_dir} is not a valid directory")
        sys.exit(1)

    lint_results = run_golangci_lint(working_dir, args.lint_command)
    os.chdir(working_dir)

    coder: Coder | None = None

    for issue in lint_results:
        coder = setup_aider(coder)
        fix_lint_issue(coder, issue, working_dir)


if __name__ == "__main__":
    main()
