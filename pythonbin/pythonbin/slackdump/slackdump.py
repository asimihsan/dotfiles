import argparse
import logging
import os
import subprocess
import sys
import tomllib as toml
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@dataclass
class Config:
    temp_dir: str
    channels: list[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        with open(config_file, "rb") as f:
            config = toml.load(f)
        backup_config = config["backup"]
        temp_dir = backup_config["temp_dir"]
        channels = backup_config["channels"]
        start_time = (
            datetime.fromisoformat(backup_config.get("start_time", ""))
            if "start_time" in backup_config
            else None
        )
        end_time = (
            datetime.fromisoformat(backup_config.get("end_time", ""))
            if "end_time" in backup_config
            else None
        )

        return cls(temp_dir, channels, start_time, end_time)


def load_config(config_file: str) -> Config:
    return Config.from_file(config_file)


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def run_command_with_live_output(command: list[str]) -> CommandResult:
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if process.stdout is None:
        return CommandResult(stdout="", stderr="Failed to open stdout", returncode=1)

    output = []
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.strip())  # Print to stdout in real-time
        sys.stdout.flush()  # Ensure it's displayed immediately
        output.append(line)  # Store the line for later use if needed

    process.wait()

    return CommandResult(
        stdout="".join(output), stderr="", returncode=process.returncode
    )


def run_slackdump(
    channel: str,
    output_dir: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> None:
    cmd = [
        "slackdump",
        "-download",
        "-export",
        output_dir,
        "-export-type",
        "standard",
    ]

    if start_time:
        cmd.extend(["-dump-from", start_time.isoformat()])
    if end_time:
        cmd.extend(["-dump-to", end_time.isoformat()])

    cmd.append(channel)

    result = run_command_with_live_output(cmd)
    if result.returncode != 0:
        logging.error(f"Error running slackdump for channel {channel}: {result.stderr}")
    else:
        logging.info(f"Successfully backed up channel {channel}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Slack Backup Script")
    parser.add_argument(
        "--config",
        default="pythonbin/slackdump/config.toml",
        help="Path to the configuration file",
    )
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)

    os.makedirs(config.temp_dir, exist_ok=True)

    for channel in config.channels:
        channel = channel.strip()
        if channel:
            run_slackdump(channel, config.temp_dir, config.start_time, config.end_time)


if __name__ == "__main__":
    main()
