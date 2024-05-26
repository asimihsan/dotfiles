import chromadb
from chromadb import PersistentClient
from pathlib import Path
import sqlite3
from typing import List, Tuple

from pythonbin.epub.db import execute_sql_get_all
from pythonbin.epub.embeddings import calculate_embeddings
from pythonbin.epub.store import get_all_sentences


def initialize_chromadb(db_path: Path, chromadb_path: Path):
    client = PersistentClient(path=str(chromadb_path))
    client.reset()  # Resetting for initialization
    collection = client.create_collection(name="ebook_embeddings")

    with sqlite3.connect(db_path) as conn:
        for sentence in get_all_sentences(conn):
            collection.add(documents=[sentence.sentence], embeddings=[sentence.embedding], ids=[str(sentence.id)])


def query_chromadb(query: str, chromadb_path: Path, n_results: int = 10) -> list[tuple[str, float]]:
    client = PersistentClient(path=str(chromadb_path))
    collection = client.get_collection(name="ebook_embeddings")

    prompt: str = f"Represent this sentence for searching relevant passages: {query}"
    query_embedding = calculate_embeddings(prompt)

    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    return list(zip(results.ids, results.distances))
