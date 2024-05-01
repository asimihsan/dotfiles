import pathlib
from typing import Generator

import pytest

from pythonbin.transcript.parser import TranscriptParser


@pytest.fixture
def test_file(tmp_path) -> Generator[pathlib.Path, None, None]:
    test_file = tmp_path / "test_file.txt"

    with open(test_file, "w") as file:
        file.write(
            """[00:00:00.22] Me:	Okay, so let's do this.
[00:00:01.64] Other(s): Yeah, let's do it."""
        )

    yield test_file

    test_file.unlink()


@pytest.fixture
def empty_file(tmp_path) -> Generator[pathlib.Path, None, None]:
    test_file = tmp_path / "test_file.txt"

    with open(test_file, "w") as file:
        file.write("")

    yield test_file

    test_file.unlink()


@pytest.fixture
def invalid_format_file(tmp_path) -> Generator[pathlib.Path, None, None]:
    test_file = tmp_path / "test_file.txt"

    with open(test_file, "w") as file:
        file.write(
            """[00:00:00.22] Me:	Okay, so let's do this.
[00:00:01.64 Other(s) Yeah, let's do it."""
        )

    yield test_file

    test_file.unlink()


def test_parser_basic(test_file):
    parser = TranscriptParser(test_file.as_posix())
    entries = list(parser.parse())
    assert len(entries) == 2
    assert entries[0].speaker == "Me"
    assert entries[0].text.startswith("Okay, so let's do this")
    assert entries[1].speaker == "Other(s)"
    assert entries[1].text.startswith("Yeah, let's do it")


def test_empty_file(empty_file):
    parser = TranscriptParser(empty_file.as_posix())
    entries = list(parser.parse())
    assert len(entries) == 0


def test_invalid_format(invalid_format_file):
    parser = TranscriptParser(invalid_format_file.as_posix())
    entries = list(parser.parse())
    assert len(entries) == 1
