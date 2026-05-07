"""Shared utility functions for agno-docs-mcp.

Provides a single source of truth for path normalisation used by both
the tools layer and the sources layer.
"""

from mcp_agno_docs.errors import ValidationError


def normalise_path(path: str) -> str:
    """Normalise a documentation path and reject traversal attempts.

    Strips leading ``/``, collapses ``.`` and empty segments, converts
    backslashes to forward slashes, and rejects any path containing ``..``.

    This is the single canonical implementation used by both
    :func:`tools.pages._get_page` and :class:`sources.local_mdx.LocalMDXSource`.

    Args:
        path: Raw path string from the client request or source lookup.

    Returns:
        Normalised POSIX-relative path.

    Raises:
        ValidationError: If *path* contains ``..`` (path traversal attempt).
    """
    clean = path.replace("\\", "/").lstrip("/")
    segments = [s for s in clean.split("/") if s not in ("", ".")]
    if ".." in segments:
        raise ValidationError(f"Path traversal rejected: {path!r}")
    return "/".join(segments)
