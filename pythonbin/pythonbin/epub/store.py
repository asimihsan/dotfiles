import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from .models import Ebook, Chapter
from .db import get_db_connection, execute_sql


def store_ebook(db_path: Path, ebook: Ebook, symbolic_name: str):
    with get_db_connection(db_path) as conn:
        ebook_id = execute_sql(
            conn, "INSERT INTO ebooks (title, symbolic_name) VALUES (?, ?)", ebook.title, symbolic_name
        )

        for chapter in ebook.chapters:
            chapter_id = execute_sql(
                conn,
                "INSERT INTO chapters (ebook_id, title, raw_content) VALUES (?, ?, ?)",
                ebook_id,
                chapter.title,
                chapter.raw_content,
            )

            for index, sentence in enumerate(chapter.sentences):
                execute_sql(
                    conn,
                    "INSERT INTO sentences (chapter_id, sentence_index, sentence) VALUES (?, ?, ?)",
                    chapter_id,
                    index,
                    sentence,
                )


@dataclass
class Sentence:
    id: int
    chapter_id: int
    sentence_index: int
    sentence: str
    embedding: bytes


def sentence_factory(cursor: sqlite3.Cursor, row: tuple) -> Sentence:
    fields = [column[0] for column in cursor.description]
    row_dict = {field: value for field, value in zip(fields, row)}
    return Sentence(**row_dict)


def get_all_sentences(conn) -> Generator[Sentence, None, None]:
    cursor = conn.cursor()
    cursor.row_factory = sentence_factory
    cursor.execute("SELECT * FROM sentences")
    for row in cursor:
        yield row
