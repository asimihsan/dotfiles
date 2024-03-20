import tree_sitter

from .build import MARKDOWN_LANGUAGE


def parse_markdown(text: str) -> tree_sitter.Tree:
    """Parse the given text using the Markdown grammar and return the syntax tree."""

    parser = tree_sitter.Parser()
    parser.set_language(MARKDOWN_LANGUAGE)
    return parser.parse(bytes(text, "utf8"))
