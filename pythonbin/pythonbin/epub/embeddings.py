import json

import numpy as np
import requests
from pathlib import Path
from .db import get_db_connection, execute_sql, execute_sql_get_all

EMBEDDING_API_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "mxbai-embed-large"


def calculate_embeddings(sentence: str, model: str = EMBEDDING_MODEL) -> bytes:
    response = requests.post(EMBEDDING_API_URL, json={"model": model, "prompt": sentence})
    response.raise_for_status()
    embedding = json.loads(response.content)["embedding"]
    embedding_array = np.array(embedding, dtype=np.float32)
    return embedding_array.tobytes()


def bytes_to_numpy_array(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def store_embeddings(db_path: Path) -> None:
    with get_db_connection(db_path) as conn:
        sentences = execute_sql_get_all(conn, "SELECT id, sentence FROM sentences WHERE embedding IS NULL")

        for sentence in sentences:
            embedding = calculate_embeddings(sentence.sentence)
            execute_sql(conn, "UPDATE sentences SET embedding = ? WHERE id = ?", embedding, sentence.id)
