"""Highlight Kedi fences with Kedi's own tree-sitter token pipeline.

Kedi code on the site is colored the way Kedi's language server and REPL color it. The tokens
come from `compute_semantic_tokens_full`, which runs tree-sitter-kedi's highlight query and
highlights embedded Python with tree-sitter-python. The build therefore always uses the grammar
of the Kedi revision it documents. Classes are Pygments short names, so the theme's code colors
apply.
"""

from __future__ import annotations

from html import escape
from typing import Any

from kedi.lsp.features import SEMANTIC_TOKEN_TYPES, compute_semantic_tokens_full

_CLASSES = {
    "namespace": "nn",
    "type": "nc",
    "class": "nc",
    "enum": "nc",
    "interface": "nc",
    "struct": "nc",
    "typeParameter": "nc",
    "parameter": "nv",
    "variable": "nv",
    "property": "na",
    "enumMember": "nl",
    "event": "n",
    "function": "nf",
    "method": "nf",
    "macro": "nf",
    "keyword": "k",
    "modifier": "k",
    "comment": "c1",
    "string": "s",
    "number": "mi",
    "regexp": "sr",
    "operator": "o",
    "decorator": "nd",
}


def _index(line: str, utf16_column: int) -> int:
    """The string index of a UTF-16 column, the unit LSP semantic tokens count in."""
    units = 0
    for index, character in enumerate(line):
        if units >= utf16_column:
            return index
        units += 2 if ord(character) > 0xFFFF else 1
    return len(line)


def highlight(source: str) -> str:
    """Kedi source as HTML, one span per semantic token."""
    lines = source.split("\n")
    spans: list[list[tuple[int, int, str]]] = [[] for _ in lines]
    data = compute_semantic_tokens_full(source, None).data
    line_number = column = 0
    for offset in range(0, len(data), 5):
        delta_line, delta_column, length, token_type = data[offset : offset + 4]
        line_number += delta_line
        column = column + delta_column if delta_line == 0 else delta_column
        line = lines[line_number]
        start, end = _index(line, column), _index(line, column + length)
        spans[line_number].append((start, end, _CLASSES[SEMANTIC_TOKEN_TYPES[token_type]]))

    rendered = []
    for line, line_spans in zip(lines, spans, strict=True):
        html, cursor = [], 0
        for start, end, class_name in sorted(line_spans):
            start = max(start, cursor)
            if end <= start:
                continue
            html.append(escape(line[cursor:start], quote=False))
            html.append(f'<span class="{class_name}">{escape(line[start:end], quote=False)}</span>')
            cursor = end
        html.append(escape(line[cursor:], quote=False))
        rendered.append("".join(html))
    return "\n".join(rendered)


def fence(
    source: str, language: str, class_name: str, options: dict[str, Any], md: Any, **kwargs: Any
) -> str:
    """A `pymdownx.superfences` formatter for `kedi` fences."""
    del language, options, md
    classes = [class_name, *kwargs["classes"]] if class_name else kwargs["classes"]
    id_value = f' id="{kwargs["id_value"]}"' if kwargs["id_value"] else ""
    class_value = f' class="{" ".join(classes)}"' if classes else ""
    attrs = "".join(f' {key}="{value}"' for key, value in kwargs["attrs"].items())
    return f"<pre{id_value}{class_value}{attrs}><code>{highlight(source)}</code></pre>"
