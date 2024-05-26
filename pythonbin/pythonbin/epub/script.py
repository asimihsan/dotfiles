#!/usr/bin/env python3

import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "ebooks.db")


def main() -> None:
    # Initialize the database
    subprocess.run(["poetry", "run", "python", "-m", "pythonbin.epub.cli", "init-db", "--db-path", DB_PATH], check=True)

    # Store an EPUB file
    subprocess.run(
        [
            "poetry",
            "run",
            "python",
            "-m",
            "pythonbin.epub.cli",
            "store-ebook",
            "--db-path",
            DB_PATH,
            "--epub-path",
            "/Users/asimi/Library/CloudStorage/Dropbox-TeamChasima/Asim Ihsan/Private/Ebooks/InformIT/Understanding Software Dynamics.epub",
            "--symbolic-name",
            "understanding_software_dynamics",
        ],
        check=True,
    )

    # Calculate embeddings
    subprocess.run(
        [
            "poetry",
            "run",
            "python",
            "-m",
            "pythonbin.epub.cli",
            "calc-embeddings",
            "--db-path",
            DB_PATH,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
