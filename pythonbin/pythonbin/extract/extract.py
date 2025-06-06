import argparse
import collections
import sys
from pathlib import Path
import os # Kept for potential future use with extract_image_block_output_dir
from contextlib import contextmanager
from typing import Iterator, Optional

# Attempt to import pypdf
try:
    from pypdf import Pdf2eader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean


# --- Core Extraction Logic ---

def _clean_extracted_elements(elements: list) -> str:
    """Cleans and joins unstructured elements."""
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

def perform_text_extraction(file_path: Path) -> str:
    """
    Extracts text from a given file path using unstructured.
    """
    print(f"Extracting from {file_path}...")
    # Note: If extract_image_block_output_dir were used, ensure it works with temp PDF paths.
    # Currently, it's commented out.
    elements = partition(
        filename=str(file_path),
        strategy="hi_res",
        # extract_image_block_types=["Image"],
        # extract_image_block_output_dir=os.path.dirname(str(file_path)), # os.path.dirname needs string
        request_timeout=20, # Increased timeout can be useful for complex documents
    )
    return _clean_extracted_elements(elements)


# --- PDF Page Range Handling ---

@contextmanager
def manage_pdf_page_range(
    original_pdf_path: Path,
    start_page: Optional[int],
    end_page: Optional[int],
) -> Iterator[Path]:
    """
    Context manager to handle PDF page range extraction.
    Yields the path to be processed (either original or a temporary page-ranged PDF).
    Cleans up the temporary PDF on exit.
    """
    is_pdf = original_pdf_path.suffix.lower() == ".pdf"
    page_range_specified = start_page is not None and end_page is not None

    if not (is_pdf and page_range_specified):
        yield original_pdf_path
        return

    if not PYPDF_AVAILABLE:
        # This specific warning is useful if general CLI validation passed (e.g. user installed pypdf mid-session for a long running script)
        # or if pypdf was optional and not checked at CLI validation.
        print(f"Warning: pypdf library is not installed. Cannot extract page range for {original_pdf_path}. Processing entire PDF.")
        yield original_pdf_path
        return

    # Page numbers are 1-indexed for user, 0-indexed for pypdf
    # Validation of start_page > 0, end_page > 0, and start_page <= end_page
    # should have happened at CLI argument parsing.
    s_page_idx = start_page - 1
    e_page_idx = end_page - 1
    temp_pdf_path: Optional[Path] = None

    try:
        print(f"Attempting to extract pages {start_page}-{end_page} from {original_pdf_path}...")
        reader = PdfReader(original_pdf_path)
        writer = PdfWriter()
        num_pages_in_pdf = len(reader.pages)

        if s_page_idx >= num_pages_in_pdf:
            print(f"Warning: start_page {start_page} is out of bounds for {original_pdf_path} which has {num_pages_in_pdf} pages. Processing entire file.")
            yield original_pdf_path
            return

        if e_page_idx >= num_pages_in_pdf:
            print(f"Warning: end_page {end_page} is out of bounds for {original_pdf_path}. Adjusting to last page: {num_pages_in_pdf}.")
            e_page_idx = num_pages_in_pdf - 1

        # This check might seem redundant if CLI validation was perfect, but good for robustness
        # especially after potential adjustments to e_page_idx.
        if s_page_idx > e_page_idx:
             print(f"Warning: Adjusted start_page {s_page_idx+1} is greater than adjusted end_page {e_page_idx+1} for {original_pdf_path}. Processing entire file.")
             yield original_pdf_path
             return

        for i in range(s_page_idx, e_page_idx + 1):
            writer.add_page(reader.pages[i])

        temp_pdf_path = original_pdf_path.with_name(
            f"{original_pdf_path.stem}_pages_{start_page}-{end_page}_temp.pdf"
        )
        with open(temp_pdf_path, "wb") as tmp_pdf_file:
            writer.write(tmp_pdf_file)
        print(f"Created temporary PDF for page range: {temp_pdf_path}")
        yield temp_pdf_path

    except Exception as e: # Catching a broad exception from pypdf or file operations
        print(f"Error during PDF page extraction for {original_pdf_path}: {e}. Processing entire file as fallback.")
        if temp_pdf_path and temp_pdf_path.exists(): # Clean up if temp file was created before error
            try:
                temp_pdf_path.unlink()
            except OSError:
                pass # Ignore errors on cleanup attempt here
        yield original_pdf_path # Fallback to original path
    finally:
        if temp_pdf_path and temp_pdf_path.exists():
            try:
                print(f"Deleting temporary PDF: {temp_pdf_path}")
                temp_pdf_path.unlink()
            except OSError as e_unlink:
                print(f"Error deleting temporary file {temp_pdf_path}: {e_unlink}")


# --- File Processing and Output ---

def _write_output_to_file(output_text: str, original_input_path: Path) -> None:
    """Writes the extracted text to a file named after the original input path."""
    output_dir = original_input_path.parent

    # Ensure output directory exists (it should, if original_input_path is valid)
    # Path(".").parent is Path(".")
    if not output_dir.exists():
        # This case should be rare for valid inputs.
        # If input is just "file.pdf", parent is "." which exists.
        # If input is "nonexistent_dir/file.pdf", script would fail earlier.
        try:
            print(f"Output directory {output_dir} does not exist. Attempting to create it.")
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error: Could not create output directory {output_dir}: {e}. Cannot write output.")
            return


    # Output file name based on original file name, add .txt extension
    output_filename = f"{original_input_path.name}.txt"
    output_path = output_dir / output_filename

    print(f"Writing to {output_path}...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
    except IOError as e:
        print(f"Error writing to {output_path}: {e}")


def process_single_file(
    original_file_path: Path,
    write_output: bool,
    start_page: Optional[int],
    end_page: Optional[int],
) -> None:
    """
    Processes a single file: extracts text (handles PDF page ranges) and writes output if requested.
    """
    with manage_pdf_page_range(original_file_path, start_page, end_page) as path_to_process:
        try:
            extracted_text = perform_text_extraction(path_to_process)
        except Exception as e: # Catch errors from unstructured partition
            print(f"Error extracting text from {path_to_process}: {e}")
            return # Skip further processing for this file

    if not write_output:
        print(extracted_text) # Print to stdout
    else:
        _write_output_to_file(extracted_text, original_file_path)


# --- Path Traversal and Main Orchestration ---

def process_paths_iteratively(
    initial_paths: list[Path],
    write_output: bool,
    start_page: Optional[int],
    end_page: Optional[int],
) -> None:
    """
    Processes a list of initial paths (files or directories).
    Directories are iterated for files; sub-directories are not processed recursively by default here.
    """
    path_queue = collections.deque(initial_paths)

    while path_queue:
        current_path = path_queue.popleft()

        if not current_path.exists():
            print(f"Error: Path {current_path} does not exist. Skipping.")
            continue

        if current_path.is_dir():
            print(f"Scanning directory: {current_path}")
            # Add files from this directory to the queue for processing
            # Sort them for consistent processing order
            for item in sorted(current_path.iterdir()):
                if item.is_file():
                    # Avoid processing our own temporary PDF files if script is run multiple times
                    # or if a previous run was interrupted.
                    if item.name.endswith("_temp.pdf") and "_pages_" in item.name:
                        print(f"Skipping potential temporary PDF file: {item}")
                        continue
                    path_queue.append(item) # Add file to the end of the queue
            continue # Move to next item in queue

        if not current_path.is_file():
            # This could be a special file type (socket, fifo, etc.) or broken symlink
            print(f"Error: Path {current_path} is not a regular file. Skipping.")
            continue

        # Now we are sure current_path is an existing, regular file
        process_single_file(current_path, write_output, start_page, end_page)


# --- Argument Parsing and Script Entry ---

def setup_arg_parser() -> argparse.ArgumentParser:
    """Sets up and returns the argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract text from files. For PDFs, a page range can be specified."
    )
    parser.add_argument(
        "paths", nargs="+", help="List of file or directory paths to process."
    )
    parser.add_argument(
        "--write", action="store_true", help="Write the output to text files (e.g., original.pdf.txt)."
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="Start page for PDF extraction (1-indexed, inclusive). Requires --end-page.",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="End page for PDF extraction (1-indexed, inclusive). Requires --start-page.",
    )
    return parser

def validate_cli_args(args: argparse.Namespace) -> None:
    """Validates command line arguments related to page ranges and pypdf availability."""
    has_start = args.start_page is not None
    has_end = args.end_page is not None

    if has_start != has_end: # XOR: one is specified but not the other
        print("Error: Both --start-page and --end-page must be provided if one is used, or neither.")
        sys.exit(1)

    if has_start: # Implies has_end is also true
        if args.start_page <= 0:
            print(f"Error: --start-page ({args.start_page}) must be a positive integer.")
            sys.exit(1)
        if args.end_page <= 0: # Should be caught by start_page > end_page if end_page is negative, but explicit check is good.
             print(f"Error: --end-page ({args.end_page}) must be a positive integer.")
             sys.exit(1)
        if args.start_page > args.end_page:
            print(f"Error: --start-page ({args.start_page}) cannot be greater than --end-page ({args.end_page}).")
            sys.exit(1)

        if not PYPDF_AVAILABLE:
            # This is a general warning at startup if page range is requested but pypdf is missing.
            print("Warning: --start-page/--end-page provided, but 'pypdf' library is not installed. Page range will be ignored for PDF files.")


def main_entry() -> None:
    """Main entry point for the script."""
    parser = setup_arg_parser()
    args = parser.parse_args()

    validate_cli_args(args)

    # Convert path strings to Path objects and sort for consistent processing order
    initial_paths = sorted([Path(p) for p in args.paths])

    process_paths_iteratively(
        initial_paths,
        args.write,
        args.start_page,
        args.end_page
    )

if __name__ == "__main__":
    main_entry()
