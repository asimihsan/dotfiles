from pathlib import Path

from pythonbin.epub.parser import read_epub


def test_read_epub():
    test_file = Path(__file__).parent / "epub30-spec.epub"
    ebook = read_epub(test_file)
    assert ebook is not None
    assert len(ebook.chapters) > 0
    for chapter in ebook.chapters:
        assert len(chapter.title) > 0
