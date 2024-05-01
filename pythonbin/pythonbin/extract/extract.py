import os
import sys

from unstructured.partition.auto import partition


def extract(path: str) -> str:
    elements = partition(
        filename=path,
        strategy='hi_res',
        # extract_image_block_types=["Image"],
        # extract_image_block_output_dir=os.path.dirname(path),
        request_timeout=10,
    )
    return "\n\n".join(str(el) for el in elements)


def run_main(path: str, write: bool = False):
    # Validate input file path
    if not os.path.exists(path):
        print(f"Error: File {path} does not exist.")
        sys.exit(1)

    if not os.path.isfile(path):
        print(f"Error: {path} is not a file.")
        sys.exit(1)

    output = extract(path)

    # Validate output file path
    if write:
        output_dir = os.path.dirname(path)
        if not os.path.exists(output_dir):
            print(f"Error: Directory {output_dir} does not exist.")
            sys.exit(1)

        output_path = os.path.splitext(path)[0] + '.txt'
        with open(output_path, 'w') as f:
            f.write(output)
    else:
        print(output)
