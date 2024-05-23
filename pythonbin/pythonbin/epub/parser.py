import concurrent.futures
import collections
import pathlib

from bs4 import BeautifulSoup

import pythonbin.epub.vebooklib as vebooklib
from .models import Ebook, Chapter, TocItem
from .utils import SpacyModel


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

    return toc_items


def _parse_chapter(toc_item: TocItem, book: vebooklib.EpubBook) -> Chapter:
    print(f"Extracting chapter: {toc_item.title}")

    book_item: vebooklib.EpubHtml = book.get_item_with_href(toc_item.filename)  # type: ignore

    content = book_item.get_body_content()
    soup = BeautifulSoup(content, "lxml")

    clean_content = soup.prettify()
    chapter = Chapter(title=toc_item.title, raw_content=clean_content)

    return chapter


def _tokenize_sentences(text: str) -> list[str]:
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return sentences


def _extract_chapters(book: vebooklib.EpubBook, toc_items: list[TocItem]) -> list[Chapter]:
    seen_filenames: set[str] = set()

    # Filter out duplicate chapters
    unique_toc_items = [
        toc_item
        for toc_item in toc_items
        if toc_item.filename not in seen_filenames and not seen_filenames.add(toc_item.filename)
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        chapters = list(executor.map(_parse_chapter, unique_toc_items, [book] * len(unique_toc_items)))

    spacy_model = SpacyModel()
    for chapter in chapters:
        doc = spacy_model.process_text(chapter.raw_content)
        sentences = [sent.text for sent in doc.sents]
        chapter.sentences = sentences

    return chapters
