import platform

from tree_sitter import Language

library_extension = "dylib" if platform.system() == "Darwin" else "so"

Language.build_library(
    # Store the library in the `build` directory
    f"build/treesitter.{library_extension}",
    # Include one or more languages
    ["external/tree-sitter-markdown"],
)

MARKDOWN_LANGUAGE = Language(f"build/treesitter.{library_extension}", "markdown")
