import argparse

from pathlib import Path
from pythonbin.epub.parser import read_epub
from pythonbin.epub.store import store_ebook
from pythonbin.epub.db import initialize_db
from pythonbin.epub.embeddings import store_embeddings
from pythonbin.epub.chromadb_utils import initialize_chromadb, query_chromadb


def main():
    parser = argparse.ArgumentParser(description="EPUB Parser and Storage")
    parser.add_argument(
        "action",
        choices=["init-db", "store-ebook", "calc-embeddings", "init-chromadb", "query-chromadb"],
        help="Action to perform",
    )
    parser.add_argument("--db-path", type=Path, required=True, help="Path to SQLite database file")
    parser.add_argument("--epub-path", type=Path, help="Path to EPUB file")
    parser.add_argument("--symbolic-name", type=str, help="Symbolic name for the EPUB file")
    parser.add_argument("--chromadb-path", type=Path, help="Path to ChromaDB storage")
    parser.add_argument("--query", type=str, help="Query text for ChromaDB")
    parser.add_argument("--n-results", type=int, default=10, help="Number of results for query")
    parser.add_argument("--context-window", type=int, default=2, help="Context window for sentence embeddings")

    args = parser.parse_args()

    if args.action == "init-db":
        initialize_db(args.db_path)
    elif args.action == "store-ebook":
        if not args.epub_path or not args.symbolic_name:
            parser.error("--epub-path and --symbolic-name are required for storing an ebook")
        ebook = read_epub(args.epub_path)
        store_ebook(args.db_path, ebook, args.symbolic_name)
    elif args.action == "calc-embeddings":
        store_embeddings(args.db_path, context_window=args.context_window)
    elif args.action == "init-chromadb":
        if not args.chromadb_path:
            parser.error("--chromadb-path is required for initializing ChromaDB")
        initialize_chromadb(args.db_path, args.chromadb_path, context_window=args.context_window)
    elif args.action == "query-chromadb":
        if not args.chromadb_path or not args.query:
            parser.error("--chromadb-path and --query are required for querying ChromaDB")
        results = query_chromadb(args.query, args.chromadb_path, args.n_results)
        # for result in results:
        #     print(f"ID: {result[0]}, Distance: {result[1]}")


if __name__ == "__main__":
    main()
