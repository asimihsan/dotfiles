#!/usr/bin/env python3

import sys
from typing import Dict
from unidecode import unidecode

import bibtexparser

def main() -> None:
    bib_input: str = sys.stdin.read()
    data: Dict[str, str] = bibtexparser.loads(bib_input).entries[0]
    title: str = unidecode(data["title"])
    author: str = unidecode(data["author"])
    year: str = unidecode(data["year"])
    filename: str = f"{title} - {author} - {year}"
    filename = filename.replace(":", " -")
    print(filename)


if __name__ == "__main__":
    main()
