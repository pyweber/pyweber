"""Merge client DOM HTML into an existing server Element tree by uuid.

Preserves Python object identity so bound handlers and ``self`` refs stay valid.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyweber.core.element import Element


def index_elements_by_uuid(root: 'Element') -> dict[str, 'Element']:
    """Walk ``root`` and map uuid → Element (skips missing/empty uuids)."""
    out: dict[str, Element] = {}

    def walk(el: 'Element') -> None:
        uid = getattr(el, 'uuid', None)
        if uid:
            out[str(uid)] = el
        for child in el.childs or []:
            walk(child)

    walk(root)
    return out


def _sync_client_fields(server_el: 'Element', client_el: 'Element') -> None:
    """Copy browser-authoritative fields onto the existing server element."""
    if client_el.value is not None:
        server_el.value = client_el.value

    for attr in ('checked', 'selected', 'disabled'):
        if attr in (client_el.attrs or {}):
            server_el.attrs[attr] = client_el.attrs[attr]
        elif attr in (server_el.attrs or {}) and attr not in (client_el.attrs or {}):
            # Client omitted boolean attr → unchecked / not selected
            if server_el.tag in ('input', 'option'):
                server_el.attrs.pop(attr, None)


def _is_top_level_client_only(client_el: 'Element', server_map: dict[str, 'Element']) -> bool:
    """True when this node is new and its parent already exists on the server (or is root)."""
    parent = client_el.parent
    if parent is None:
        return False
    parent_uid = getattr(parent, 'uuid', None)
    if not parent_uid:
        return False
    return str(parent_uid) in server_map


def merge_client_dom(
    server_root: 'Element',
    client_html: str,
    *,
    include_uuid: bool = True,
) -> None:
    """Merge parsed client HTML into ``server_root`` without replacing known nodes.

    - Matching uuids: update value / form-ish attrs in place.
    - Client-only uuids (e.g. JS inject): graft the new subtree under the matching
      server parent.
    - Server-only uuids: left untouched (next diff can reconcile the browser).
    """
    from pyweber.core.element import Element

    if not client_html or not client_html.strip():
        return

    client_root = Element.from_html(client_html, include_uuid=include_uuid)
    server_map = index_elements_by_uuid(server_root)
    client_map = index_elements_by_uuid(client_root)

    for uid, server_el in list(server_map.items()):
        client_el = client_map.get(uid)
        if client_el is not None:
            _sync_client_fields(server_el, client_el)

    for uid, client_el in client_map.items():
        if uid in server_map:
            continue
        if not _is_top_level_client_only(client_el, server_map):
            continue

        parent_uid = str(client_el.parent.uuid)
        server_parent = server_map[parent_uid]
        grafted = client_el.clone
        grafted.parent = None
        server_parent.add_child(grafted)
        server_map.update(index_elements_by_uuid(grafted))
