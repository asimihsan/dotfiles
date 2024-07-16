import collections
import os
import sys
from pathlib import Path

from unstructured.partition.auto import partition, partition_pdf, partition_epub
from unstructured.cleaners.core import clean


def extract(path: Path) -> str:
    print(f"Extracting {path}...")

    ext = path.suffix.lower()
    if ext == ".pdf":
        method = partition_pdf
    elif ext == ".epub":
        method = partition_epub
    else:
        method = partition

    elements = method(
        filename=str(path),
        strategy="hi_res",
        # extract_image_block_types=["Image"],
        # extract_image_block_output_dir=os.path.dirname(path),
        request_timeout=10,
    )
    return "\n\n".join(
        clean(
            str(el),
            bullets=False,
            extra_whitespace=True,
            dashes=True,
            trailing_punctuation=True,
        )
        for el in elements
    )


def run_main(paths: list[str], write: bool = False):
    deque = collections.deque((Path(p) for p in paths))

    while deque:
        path = Path(deque.popleft())

        if not path.exists():
            print(f"Error: File {path} does not exist.")
            continue

        if path.is_dir():
            for p in path.iterdir():
                if p.is_file():
                    deque.append(p)
            continue

        if not path.is_file():
            print(f"Error: {path} is not a file.")
            continue

        do_extract(path, write=write)


def do_extract(path: Path, write: bool = False):
    output = extract(path)

    if not write:
        print(output)
        return

    output_dir = path.parent
    if not output_dir.exists():
        print(f"Error: Directory {output_dir} does not exist.")
        sys.exit(1)

    # keep original extension, add .txt on end
    output_path = output_dir / f"{path}.txt"
    print(f"Writing to {output_path}...")

    with open(output_path, "w") as f:
        f.write(output)
