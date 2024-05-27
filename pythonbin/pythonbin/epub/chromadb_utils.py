import chromadb
from litellm import completion
import numpy as np
from chromadb import PersistentClient, Settings
from pathlib import Path
import sqlite3
from typing import List, Tuple

from pythonbin.epub.db import execute_sql_get_all
from pythonbin.epub.embeddings import calculate_embeddings
from pythonbin.epub.store import get_all_sentences, get_total_sentences


def initialize_chromadb(db_path: Path, chromadb_path: Path, context_window: int = 2):
    client = PersistentClient(
        path=str(chromadb_path),
        settings=Settings(
            allow_reset=True,
        ),
    )
    client.reset()  # Resetting for initialization
    collection = client.create_collection(name="ebook_embeddings")

    with sqlite3.connect(db_path) as conn:
        total_sentences = get_total_sentences(conn)

        for i, sentence in enumerate(get_all_sentences(conn, context_window=context_window)):
            if i % 100 == 0:
                print(f"Processed {i}/{total_sentences} sentences.")
            collection.add(
                documents=[sentence.sentence_context], embeddings=[sentence.embedding_list], ids=[str(sentence.id)]
            )


def query_chromadb(query: str, chromadb_path: Path, n_results: int = 10) -> list[tuple[str, float]]:
    client = PersistentClient(path=str(chromadb_path))
    collection = client.get_collection(name="ebook_embeddings")

    print(f"Original query: {query}")
    expanded_query = expand_query(query)
    print(f"Expanded query: {expanded_query}")

    prompt: str = f"Represent this query for searching relevant passages: {expanded_query}"
    query_embedding = calculate_embeddings(prompt)
    query_embedding_list = np.frombuffer(query_embedding, dtype=np.float32).tolist()

    results = collection.query(query_embeddings=[query_embedding_list], n_results=n_results)
    if results is None:
        return []
    for x in results["documents"]:
        for y in x:
            print(y)
            print("---")

    # return list(zip(results.ids, results.distances))


def expand_query(query: str, model: str = "ollama/llama3") -> str:
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": "Please generate a paragraph of text that answers the question."},
            {"role": "user", "content": query},
        ],
        api_base="http://localhost:11434",
    )
    result = response.choices[0].message.content
    return result
