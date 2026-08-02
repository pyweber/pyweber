"""Upload MIME sniffing helpers."""

from __future__ import annotations

from typing import Iterable

# (mime, extensions, magic prefixes)
_SIGNATURES: list[tuple[str, tuple[str, ...], tuple[bytes, ...]]] = [
    ('image/png', ('png',), (b'\x89PNG\r\n\x1a\n',)),
    ('image/jpeg', ('jpg', 'jpeg'), (b'\xff\xd8\xff',)),
    ('image/gif', ('gif',), (b'GIF87a', b'GIF89a')),
    ('application/pdf', ('pdf',), (b'%PDF',)),
    ('application/zip', ('zip', 'docx', 'xlsx', 'pptx'), (b'PK\x03\x04', b'PK\x05\x06')),
    ('image/webp', ('webp',), (b'RIFF',)),  # needs WEBP at offset 8 — checked below
    ('text/plain', ('txt', 'csv', 'md'), ()),
]


class UploadValidationError(ValueError):
    pass


def sniff_mime(content: bytes | None) -> str | None:
    if not content:
        return None
    for mime, _, magics in _SIGNATURES:
        if not magics:
            continue
        for magic in magics:
            if content.startswith(magic):
                if mime == 'image/webp':
                    if len(content) >= 12 and content[8:12] == b'WEBP':
                        return mime
                    continue
                return mime
    # UTF-8 text heuristic
    try:
        content[:512].decode('utf-8')
        return 'text/plain'
    except UnicodeDecodeError:
        return None


def validate_upload(
    content: bytes,
    *,
    filename: str | None = None,
    declared_type: str | None = None,
    allowed: Iterable[str] | None = None,
) -> str:
    """Return detected MIME or raise UploadValidationError."""
    detected = sniff_mime(content)
    allowed_set = {a.lower() for a in allowed} if allowed is not None else None

    if allowed_set is not None:
        if detected and detected.lower() in allowed_set:
            return detected
        if declared_type and declared_type.lower() in allowed_set and detected is None:
            return declared_type
        raise UploadValidationError(
            f'Upload rejected: detected={detected!r}, declared={declared_type!r}, '
            f'allowed={sorted(allowed_set)}'
        )

    if declared_type and detected and declared_type.split(';')[0].strip().lower() != detected.lower():
        # Soft mismatch: still allow but prefer detected
        return detected

    return detected or (declared_type or 'application/octet-stream')
