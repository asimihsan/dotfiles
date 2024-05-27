import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import numpy as np

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
    sentence_context: str = ""

    @property
    def embedding_list(self) -> list[float]:
        return np.frombuffer(self.embedding, dtype=np.float32).tolist()


def sentence_factory(cursor: sqlite3.Cursor, row: tuple) -> Sentence:
    fields = [column[0] for column in cursor.description]
    row_dict = {field: value for field, value in zip(fields, row)}
    return Sentence(**row_dict)


def get_total_sentences(conn: sqlite3.Connection, embedding_missing: bool = False) -> int:
    cursor = conn.cursor()
    if embedding_missing:
        cursor.execute("SELECT COUNT(*) FROM sentences WHERE embedding IS NULL")
    else:
        cursor.execute("SELECT COUNT(*) FROM sentences")
    total_sentences = cursor.fetchone()[0]
    return total_sentences


def get_sentence_context(conn: sqlite3.Connection, chapter_id: int, sentence_index: int, window_size: int) -> str:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sentence FROM sentences
        WHERE chapter_id = ? AND sentence_index BETWEEN ? AND ?
        ORDER BY sentence_index
        """,
        (chapter_id, sentence_index - window_size, sentence_index + window_size),
    )
    context_sentences = [row[0] for row in cursor.fetchall()]
    return " ".join(context_sentences)


def get_all_sentences(
    conn, embedding_missing: bool = False, context_window: int = 2
) -> Generator[Sentence, None, None]:
    cursor = conn.cursor()
    cursor.row_factory = sentence_factory

    if embedding_missing:
        cursor.execute("SELECT * FROM sentences WHERE embedding IS NULL")
    else:
        cursor.execute("SELECT * FROM sentences")

    for row in cursor:
        sentence = row
        sentence.sentence_context = get_sentence_context(
            conn, sentence.chapter_id, sentence.sentence_index, context_window
        )
        yield sentence
