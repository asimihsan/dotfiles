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

    # Increase cache size to 32MB to keep more pages in memory.
    # Default is -2000, 2000 pages of 1KB each, which is 2MB.
    conn.execute("PRAGMA cache_size = -32000;")

    # Increase mmap size to 30GB to allow more memory mapping and reduce system calls.
    conn.execute("PRAGMA mmap_size = 30000000000;")

    # Use memory for temp store to reduce disk I/O.
    conn.execute("PRAGMA temp_store = MEMORY;")

    # Use Write-Ahead Logging (WAL) mode for better concurrency when reading and writing.
    conn.execute("PRAGMA journal_mode = WAL;")

    # Relax the synchronous setting to improve write performance.
    # WAL mode is always consistent with NORMAL, but may lose durability across power loss, i.e. may
    # rollback following a power loss. FULL is the most durable but also the slowest.
    conn.execute("PRAGMA synchronous = NORMAL;")

    # Limit the journal size to 6MB, default is unlimited. This can help reduce disk space usage.
    conn.execute("PRAGMA journal_size_limit = 6144000;")

    # Enable incremental auto-vacuum mode to avoid long pauses during vacuuming.
    conn.execute("PRAGMA auto_vacuum = INCREMENTAL;")

    try:
        yield conn
    finally:
        # Collect statistics to help the query planner.
        conn.execute("PRAGMA optimize;")

        conn.close()


def incremental_vacuum(conn: sqlite3.Connection, n_pages: int = 100) -> None:
    conn.execute(f"PRAGMA incremental_vacuum({n_pages});")


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
