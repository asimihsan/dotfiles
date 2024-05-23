import pathlib

import pythonbin.epub.vebooklib as vebooklib
from pythonbin.epub.parser import read_epub

book = read_epub(
    pathlib.Path(
        "/Users/asimi/Library/CloudStorage/Dropbox-TeamChasima/Asim Ihsan/Private/Ebooks/InformIT/Understanding Software Dynamics.epub"
    )
)


cnt = 0
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        print(f"Document: {item.get_name()}")
        if hasattr(item, "get_title"):
            print(f"Title: {item.get_title()}")
        print(item.get_body_content())
        cnt += 1
        if cnt > 20:
            break
