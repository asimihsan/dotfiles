import collections
import pathlib

from bs4 import BeautifulSoup

import pythonbin.epub.vebooklib as vebooklib
from ebooklib import epub
from .models import Ebook, Chapter, Page, TocItem
from typing import List


def read_epub(file_path: pathlib.Path) -> Ebook:
    book = vebooklib.read_epub(str(file_path))
    title = book.get_metadata("DC", "title")[0][0]
    ebook = Ebook(title=title)

    # Extract the table of contents (TOC)
    toc_items = _extract_toc(book)
    chapters = _extract_chapters(book, toc_items)
    ebook.chapters.extend(chapters)

    return ebook


def _extract_toc(book) -> list[TocItem]:
    toc_items: list[TocItem] = []
    deque = collections.deque()
    deque.extend(book.toc)
    while deque:
        toc_item = deque.popleft()
        if isinstance(toc_item, tuple):
            toc_items.append(
                TocItem(
                    href=toc_item[0].href,
                    title=toc_item[0].title,
                )
            )
            for toc_item in toc_item[1][::-1]:
                deque.appendleft(toc_item)
        else:
            toc_items.append(
                TocItem(
                    href=toc_item.href,
                    title=toc_item.title,
                )
            )

    for toc_item in toc_items:
        print(toc_item)

    return toc_items


def _extract_chapters(book: vebooklib.EpubBook, toc_items: List[dict]) -> List[Chapter]:
    chapters = []
    chapter_number = 1
    for toc_item in toc_items:
        chapter = Chapter(number=chapter_number, title=toc_item["title"])
        chapters.append(chapter)
        chapter_number += 1
    return chapters
