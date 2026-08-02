"""Pluggable HTML parse backends for Pyweber Element trees.

Default backend is the stdlib ``html.parser`` (pure Python, serverless-friendly).
``lxml`` remains available as an optional extra for maximum parse performance.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Literal

HtmlParserName = Literal['stdlib', 'lxml']

VOID_ELEMENTS = frozenset({
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
})


@dataclass
class ParsedNode:
    """Backend-agnostic HTML tree node consumed by ``Element._create_element``."""

    tag: str
    attrib: dict[str, str] = field(default_factory=dict)
    text: str | None = None
    children: list['ParsedNode'] = field(default_factory=list)
    tail: str | None = None
    is_comment: bool = False

    def getchildren(self) -> list['ParsedNode']:
        return self.children


class HtmlParseBackend(ABC):
    name: HtmlParserName

    @abstractmethod
    def parse(self, html: str) -> ParsedNode:
        """Parse HTML markup into a ``ParsedNode`` tree."""


class StdlibHtmlBackend(HtmlParseBackend):
    """Pure-Python HTML parser based on ``html.parser.HTMLParser``."""

    name: HtmlParserName = 'stdlib'

    def parse(self, html: str) -> ParsedNode:
        builder = _StdlibTreeBuilder()
        builder.feed(html)
        builder.close()
        if builder.root is None:
            raise ValueError('Failed to parse HTML: empty or invalid markup')
        return builder.root


class _StdlibTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root: ParsedNode | None = None
        self._stack: list[ParsedNode] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrib = {
            key: ('' if value is None else value)
            for key, value in attrs
        }
        node = ParsedNode(tag=tag.lower(), attrib=attrib)
        self._attach(node)

        if tag.lower() in VOID_ELEMENTS:
            return

        self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrib = {
            key: ('' if value is None else value)
            for key, value in attrs
        }
        node = ParsedNode(tag=tag.lower(), attrib=attrib)
        self._attach(node)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            return

        while self._stack:
            node = self._stack.pop()
            if node.tag == tag:
                break

    def handle_data(self, data: str):
        if not self._stack:
            return

        parent = self._stack[-1]
        if parent.children:
            last = parent.children[-1]
            last.tail = (last.tail or '') + data
        else:
            parent.text = (parent.text or '') + data

    def handle_comment(self, data: str):
        node = ParsedNode(tag='comment', text=data, is_comment=True)
        self._attach(node)

    def _attach(self, node: ParsedNode):
        if self._stack:
            self._stack[-1].children.append(node)
        elif self.root is None:
            self.root = node
        else:
            # Multiple top-level nodes: wrap under a synthetic fragment root.
            if self.root.tag != '#fragment':
                fragment = ParsedNode(tag='#fragment', children=[self.root])
                self.root = fragment
            self.root.children.append(node)


class LxmlHtmlBackend(HtmlParseBackend):
    """Optional ``lxml.html`` backend. Requires ``pip install pyweber[fast-html]``."""

    name: HtmlParserName = 'lxml'

    def parse(self, html: str) -> ParsedNode:
        try:
            import lxml.html as html_mod
            from lxml.html import fromstring
        except ImportError as exc:
            raise ImportError(
                "lxml is not installed. Install with: pip install 'pyweber[fast-html]'"
            ) from exc

        root = fromstring(html)
        return self._convert(root, html_mod)

    def _convert(self, node, html_mod) -> ParsedNode:
        if isinstance(node, html_mod.HtmlComment):
            return ParsedNode(
                tag='comment',
                text=str(node.text) if node.text is not None else '',
                is_comment=True,
                tail=str(node.tail) if node.tail else None,
            )

        attrib = {str(k): str(v) if v is not None else '' for k, v in node.attrib.items()}
        parsed = ParsedNode(
            tag=str(node.tag),
            attrib=attrib,
            text=str(node.text) if node.text is not None else None,
            tail=str(node.tail) if node.tail else None,
        )
        for child in node:
            parsed.children.append(self._convert(child, html_mod))
        return parsed


_BACKENDS: dict[HtmlParserName, type[HtmlParseBackend]] = {
    'stdlib': StdlibHtmlBackend,
    'lxml': LxmlHtmlBackend,
}

_active_backend: HtmlParseBackend | None = None


def _resolve_default_backend_name() -> HtmlParserName:
    env = (os.environ.get('PYWEBER_HTML_PARSER') or 'stdlib').strip().lower()
    if env not in _BACKENDS:
        raise ValueError(
            f"Unknown PYWEBER_HTML_PARSER={env!r}. Expected one of: {', '.join(_BACKENDS)}"
        )
    return env  # type: ignore[return-value]


def get_html_parser_backend() -> HtmlParseBackend:
    global _active_backend
    if _active_backend is None:
        _active_backend = _BACKENDS[_resolve_default_backend_name()]()
    return _active_backend


def set_html_parser_backend(name: HtmlParserName | HtmlParseBackend) -> HtmlParseBackend:
    """Select the active HTML parse backend (``'stdlib'`` or ``'lxml'``)."""
    global _active_backend
    if isinstance(name, HtmlParseBackend):
        _active_backend = name
        return _active_backend

    if name not in _BACKENDS:
        raise ValueError(f"Unknown HTML parser backend: {name!r}")

    _active_backend = _BACKENDS[name]()
    return _active_backend


def reset_html_parser_backend() -> None:
    """Reset to the environment/default backend (mainly for tests)."""
    global _active_backend
    _active_backend = None


def parse_html(html: str, backend: HtmlParseBackend | None = None) -> ParsedNode:
    parser = backend or get_html_parser_backend()
    root = parser.parse(html)
    # Unwrap accidental fragment wrappers when a single real root exists.
    if root.tag == '#fragment' and len(root.children) == 1:
        return root.children[0]
    return root
