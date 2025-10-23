import argparse
import os
import pathlib
import shutil
import signal
import tempfile
import time

import psutil
import zstandard as zstd


def main(logs_dir: pathlib.Path, compression_level: int, modification_time_limit: int) -> None:
    """
    Compress log files in the logs directory that have not been modified in the last 'modification_time_limit' minutes.

    :param logs_dir: Directory where log files are stored.
    :param compression_level: Zstandard compression level.
    :param modification_time_limit: Time limit in minutes for last modification.
    :return: None
    """
    log_files = (f for f in logs_dir.iterdir() if f.is_file())
    for log_file in log_files:
        # If already compressed, skip
        if log_file.suffix == ".zst":
            continue

        # Check if the file was last modified more than 'modification_time_limit' minutes ago
        if time.time() - os.path.getmtime(log_file) > modification_time_limit * 60:
            # Check if any process has an open file handle to the log file
            if not is_file_open(log_file):
                # Compress the file
                compress_file(log_file, compression_level)


def is_file_open(file_path: pathlib.Path) -> bool:
    """
    Check if any process has an open file handle to the file.

    :param file_path: Path to the file.
    :return: True if any process has an open file handle to the file, False otherwise.
    """
    for proc in psutil.process_iter(["open_files"]):
        try:
            for proc_open_file_path in proc.info["open_files"] or []:
                if file_path == pathlib.Path(proc_open_file_path.path):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process no longer exists or access is denied; skip it
            continue
    return False


def compress_file(file_path: pathlib.Path, compression_level: int) -> None:
    """
    Compress the file using zstandard.

    :param file_path: Path to the file.
    :param compression_level: Zstandard compression level.
    :return: None
    """

    print(f"Compressing {file_path}...")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        # Initialize zstandard compressor
        cctx = zstd.ZstdCompressor(level=compression_level, write_content_size=True, write_checksum=True, threads=-1)
        with file_path.open("rb") as source:
            source_size = file_path.stat().st_size
            with cctx.stream_writer(tmp_file, size=source_size) as compressor:
                shutil.copyfileobj(source, compressor)

    # Verify the compressed file
    if verify_compressed_file(pathlib.Path(tmp_file.name)):
        # Move the compressed file to the logs directory. Keep the existing suffix. e.g.
        # foo.log -> foo.log.zst
        compressed_file_path = file_path.with_suffix(file_path.suffix + ".zst")

        shutil.move(tmp_file.name, compressed_file_path)
        shutil.copystat(file_path, compressed_file_path)

        os.remove(file_path)

    if os.path.exists(tmp_file.name):
        os.remove(tmp_file.name)


def verify_compressed_file(file_path: pathlib.Path) -> bool:
    """
    Verify the compressed file.

    :param file_path: Path to the file.
    :return: True if the file is a valid zstandard compressed file, False otherwise.
    """

    try:
        dctx = zstd.ZstdDecompressor()
        with file_path.open("rb") as compressed_file:
            dctx.stream_reader(compressed_file)
        return True
    except zstd.ZstdError:
        return False


def parse_arguments() -> argparse.Namespace:
    """
    Parse the command-line arguments.

    :return: argparse.Namespace
    """

    parser = argparse.ArgumentParser(description="Compress log files.")
    parser.add_argument(
        "--logs-dir", type=str, default="~/logs", required=False, help="Directory where log files are stored."
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        default=7,
        required=False,
        help="Zstandard compression level.",
    )
    parser.add_argument(
        "--modification-time-limit",
        type=int,
        default=5,
        required=False,
        help="Time limit in minutes for last modification.",
    )
    return parser.parse_args()


def signal_handler(signum, frame) -> None:
    """
    Handle CTRL-C (SIGINT) gracefully.

    :param signum: Signal number
    :param frame: Current stack frame
    :return: None
    """

    print("Script interrupted. Please rerun the script to ensure all files are processed.")
    exit(1)


def run_main() -> None:
    """
    Run the main function.

    :return: None
    """

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Parse the command-line arguments
    args = parse_arguments()

    # Expand the user's home directory path
    logs_dir = pathlib.Path(args.logs_dir).expanduser()

    # Call the main function
    main(logs_dir, args.compression_level, args.modification_time_limit)


if __name__ == "__main__":
    run_main()
