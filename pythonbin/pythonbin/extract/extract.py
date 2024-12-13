import argparse
import collections
import sys
from pathlib import Path

from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean


def extract(path: Path) -> str:
    print(f"Extracting {path}...")

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


def run_main(paths: list[Path], write: bool = False):
    deque = collections.deque(paths)

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


def parse_arguments():
    parser = argparse.ArgumentParser(description="Extract text from files.")
    parser.add_argument(
        "paths", nargs="+", help="List of file or directory paths to process."
    )
    parser.add_argument(
        "--write", action="store_true", help="Write the output to text files."
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    paths = [Path(p) for p in args.paths]
    run_main(paths, write=args.write)


if __name__ == "__main__":
    main()
