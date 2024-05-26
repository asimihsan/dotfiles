import concurrent.futures
import json
import threading
import time
import os

import numpy as np
import requests
from pathlib import Path
from .db import get_db_connection, execute_sql, execute_sql_get_all
from .store import get_all_sentences, get_total_sentences

EMBEDDING_API_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "mxbai-embed-large"


def calculate_embeddings(sentence: str, model: str = EMBEDDING_MODEL) -> bytes:
    response = requests.post(EMBEDDING_API_URL, json={"model": model, "prompt": sentence})
    response.raise_for_status()
    embedding = json.loads(response.content)["embedding"]
    embedding_array = np.array(embedding, dtype=np.float32)
    return embedding_array.tobytes()


class SentenceProcessor:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.counter_lock = threading.Lock()
        self.processed_sentences = 0
        self.stop_event = threading.Event()

    def __enter__(self):
        self.conn = get_db_connection(self.db_path).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.__exit__(exc_type, exc_val, exc_tb)

    def process_sentence(self, sentence) -> None:
        embedding = calculate_embeddings(sentence.sentence)
        execute_sql(self.conn, "UPDATE sentences SET embedding = ? WHERE id = ?", embedding, sentence.id)
        with self.counter_lock:
            self.processed_sentences += 1

    def print_status(self, total_sentences: int) -> None:
        while not self.stop_event.is_set():
            with self.counter_lock:
                print(f"Processed {self.processed_sentences}/{total_sentences} sentences.")
            time.sleep(1)

    def start_processing(self) -> None:
        with get_db_connection(self.db_path) as conn:
            total_sentences = get_total_sentences(conn, embedding_missing=True)
            sentences = get_all_sentences(conn, embedding_missing=True)
            workers = 1
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                # Start a separate thread for printing the status
                status_thread = threading.Thread(target=self.print_status, args=(total_sentences,), daemon=True)
                status_thread.start()

                # Submit tasks to the executor
                futures = {executor.submit(self.process_sentence, sentence) for sentence in sentences}

                # Ensure all futures are completed
                for future in concurrent.futures.as_completed(futures):
                    future.result()  # Retrieve any exception raised by the task

                # Signal the status thread to stop after processing
                self.stop_event.set()
                status_thread.join()


def bytes_to_numpy_array(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def store_embeddings(db_path: Path) -> None:
    with SentenceProcessor(db_path) as processor:
        processor.start_processing()
