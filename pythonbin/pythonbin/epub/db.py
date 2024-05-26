import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any
from collections import namedtuple


def namedtuple_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Any:
    fields = [column[0] for column in cursor.description]
    return namedtuple("Row", fields)(*row)


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {column[0]: value for column, value in zip(cursor.description, row)}


@contextmanager
def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def execute_sql(conn: sqlite3.Connection, sql: str, *args) -> int | None:
    cursor = conn.cursor()
    cursor.row_factory = namedtuple_factory
    cursor.execute(sql, args)
    conn.commit()
    return cursor.lastrowid


def execute_sql_get_all(conn: sqlite3.Connection, sql: str, *args) -> Generator[dict[str, Any], None, None]:
    cursor = conn.cursor()
    cursor.row_factory = dict_factory
    cursor.execute(sql, args)
    for row in cursor:
        yield row


def initialize_db(db_path: Path) -> None:
    with get_db_connection(db_path) as conn:
        execute_sql(
            conn,
            """
            CREATE TABLE IF NOT EXISTS ebooks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                symbolic_name TEXT UNIQUE NOT NULL
            )
        """,
        )

        execute_sql(
            conn,
            """
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY,
                ebook_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                FOREIGN KEY (ebook_id) REFERENCES ebooks (id)
            )
        """,
        )

        execute_sql(
            conn,
            """
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY,
                chapter_id INTEGER NOT NULL,
                sentence_index INTEGER NOT NULL,
                sentence TEXT NOT NULL,
                embedding BLOB,
                FOREIGN KEY (chapter_id) REFERENCES chapters (id)
            )
        """,
        )

        execute_sql(
            conn,
            """
            CREATE INDEX IF NOT EXISTS idx_sentence_index ON sentences (sentence_index)
        """,
        )
