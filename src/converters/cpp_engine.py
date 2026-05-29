"""C/C++ source → Markdown converter, a Python port of ah01/h2md.

Extracts ``/** ... */`` block comments plus the one line of code that follows each,
turning code lines into Markdown headers and emitting the comment bodies (which are
assumed to already contain Markdown). Files with no doc blocks fall back to a single
fenced code block of the whole source.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

C_EXTENSION = ".c"

# Emoji header prefixes, matching h2md's c/cpp patterns.
PREFIX_C_FUNCTION = "🔹 "
PREFIX_VARIABLE = "🔧 "
PREFIX_CONSTRUCTOR = "💡 "
PREFIX_TYPEDEF = "🔘 "
PREFIX_METHOD = "Ⓜ️ "


class _Block:
    """A doc comment block plus the code line that follows it."""

    def __init__(self) -> None:
        self.text: list[str] = []
        self.code: str = ""
        self.header: str | None = None


def _trim_text(line: str) -> str:
    """Strip a leading '* ' (or lone '*') from a comment body line."""
    text = line.strip()
    if text.startswith("* "):
        text = text[2:]
    if text == "*":
        text = ""
    return text


def _trim_code(line: str) -> str:
    """Trim whitespace and strip trailing semicolons from a code line."""
    code = line.strip()
    while code.endswith(";"):
        code = code[:-1]
    return code.strip()


def _parse_blocks(text: str) -> list[_Block]:
    """Tokenize source into doc-comment blocks (h2md tokenizer)."""
    lines = text.split("\n")
    blocks: list[_Block] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("/**"):
            i += 1
            continue

        block = _Block()
        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            i += 1
            if stripped.startswith("*/") or stripped.startswith("**/"):
                break
            block.text.append(_trim_text(stripped))

        if i < len(lines):
            block.code = _trim_code(lines[i])
            i += 1
        blocks.append(block)
    return blocks


def _apply_cpp_pattern(block: _Block, class_name: str) -> str:
    """Compute header for a code line using h2md's cpp pattern. Returns class name."""
    code = block.code
    if code.startswith("class"):
        class_name = code[6:]
        block.header = class_name
        return class_name
    if "(" in code:
        if class_name and class_name in code:
            block.header = PREFIX_CONSTRUCTOR + code
        elif "typedef " in code:
            block.header = PREFIX_TYPEDEF + code
        else:
            block.header = PREFIX_METHOD + code
        return class_name
    if code.startswith("typedef"):
        block.header = None  # suppressed
        return class_name
    block.header = PREFIX_VARIABLE + code
    return class_name


def _apply_c_pattern(block: _Block) -> None:
    """Compute header for a code line using h2md's c pattern."""
    block.header = (PREFIX_C_FUNCTION if "(" in block.code else PREFIX_VARIABLE) + block.code


class _Generator:
    """Builds Markdown from parsed blocks (h2md generator), anchors disabled."""

    def __init__(self, is_c: bool) -> None:
        self.is_c = is_c
        self.level = 0
        self.in_code_block = False
        self.doc: list[str] = []
        self._class_name = ""

    def generate(self, blocks: list[_Block]) -> str:
        for block in blocks:
            self._add_block(block)
        return "\n".join(self.doc)

    def _add_block(self, block: _Block) -> None:
        if block.code != "":
            if self.is_c:
                _apply_c_pattern(block)
            else:
                self._class_name = _apply_cpp_pattern(block, self._class_name)
            self.doc.append("#" * (self.level + 1) + " " + (block.header or block.code))
            self.doc.append("")
            self.doc.append("```cpp")
            self.doc.append(block.code)
            self.doc.append("```")
            self.doc.append("")
            self._add_lines(block.text, relative=True)
        else:
            self._add_lines(block.text, relative=False)
        self.doc.append("")

    def _add_lines(self, lines: list[str], relative: bool) -> None:
        for line in lines:
            self._add_text_line(line, relative)

    def _add_text_line(self, text: str, relative: bool) -> None:
        if text.startswith("```"):
            self.in_code_block = not self.in_code_block
        if self.in_code_block:
            self.doc.append(text)
            return
        if text.startswith("#"):
            if relative:
                self.doc.append("#" * (self.level + 1) + text)
            else:
                prefix = text[: text.find(" ")] if " " in text else text
                self.level = len(prefix)
                self.doc.append(text)
        else:
            self.doc.append(text)


def _fallback_code_fence(text: str, is_c: bool) -> str:
    """Wrap the whole source in a fenced code block when no doc blocks exist."""
    lang = "c" if is_c else "cpp"
    return f"```{lang}\n{text.rstrip()}\n```\n"


def convert_file(filepath: Path) -> str:
    """Convert a C/C++ source/header file to Markdown. Returns Markdown, or '[ERROR] ...'."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        is_c = filepath.suffix.lower() == C_EXTENSION
        blocks = _parse_blocks(text)
        if not blocks:
            return _fallback_code_fence(text, is_c)
        return _Generator(is_c).generate(blocks)
    except Exception as e:
        logger.error("C/C++ conversion failed: %s", type(e).__name__)
        return f"[ERROR] Could not convert this file ({type(e).__name__})."
