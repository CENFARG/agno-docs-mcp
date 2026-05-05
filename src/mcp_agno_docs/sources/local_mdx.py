"""Filesystem adapter that reads ``.mdx`` files from a local directory.

Walks a ``root_path`` recursively, parses YAML frontmatter from each
``.mdx`` file, and returns :class:`DocPage` objects. Implements the
:class:`DocSource` abstract port.

All blocking disk I/O is wrapped in :func:`asyncio.to_thread` so the
event loop is never blocked.
"""

import asyncio
import logging
from pathlib import Path

import yaml

from mcp_agno_docs.errors import PageNotFound, PageInvalid, StartupError
from mcp_agno_docs.models import (
    DocFrontmatter,
    DocPage,
    IndexDocument,
    LocalSourceConfig,
)
from mcp_agno_docs.sources.base import DocSource

logger = logging.getLogger(__name__)


class LocalMDXSource(DocSource):
    """Parse and serve documentation pages from a local directory of .mdx files.

    Args:
        config: Configuration with ``root_path`` pointing to the docs root.

    Raises:
        StartupError: If ``root_path`` does not exist or is not a directory.
    """

    def __init__(self, config: LocalSourceConfig) -> None:
        self._root = config.root_path
        self._pages: dict[str, DocPage] = {}
        self._invalid: dict[str, str] = {}
        self._loaded = False

    # ---- DocSource interface ----

    async def load(self) -> None:
        """Walk *root_path* for ``.mdx`` files and parse frontmatter."""
        if not self._root.is_dir():
            raise StartupError(f"Docs root path is not a directory: {self._root}")

        def _scan() -> None:
            pages: dict[str, DocPage] = {}
            invalid: dict[str, str] = {}
            for mdx_file in self._root.rglob("*.mdx"):
                _process_file(mdx_file, self._root, pages, invalid)
            # Assign atomically after the full scan.
            self._pages = pages
            self._invalid = invalid
            self._loaded = True

        await asyncio.to_thread(_scan)

    def get_page(self, path: str) -> DocPage:
        """Retrieve a page by its normalised POSIX path.

        Raises:
            PageNotFound: Path not in loaded pages.
            PageInvalid: Path exists but was marked invalid.
        """
        normalised = _normalise_path(path)
        if normalised in self._invalid:
            raise PageInvalid(
                f"Page {normalised} is invalid: {self._invalid[normalised]}"
            )
        try:
            return self._pages[normalised]
        except KeyError:
            raise PageNotFound(f"Page not found: {normalised}")

    def list_pages(self) -> list[str]:
        """Return sorted list of all known page paths."""
        return sorted(self._pages.keys())

    def iter_index_documents(self):
        """Yield :class:`IndexDocument` for every valid loaded page."""
        for page in self._pages.values():
            yield IndexDocument(
                path=page.path,
                title=page.frontmatter.title,
                description=page.frontmatter.description,
                content=page.content,
                keywords=page.frontmatter.keywords,
            )


# ---- Internal helpers ----


def _process_file(
    mdx_file: Path,
    root: Path,
    pages: dict[str, DocPage],
    invalid: dict[str, str],
) -> None:
    """Parse a single .mdx file and store the result in *pages* or *invalid*."""
    # Skip hidden / dot-files.
    if mdx_file.name.startswith("."):
        return

    rel = mdx_file.relative_to(root)
    posix_path = rel.as_posix()

    try:
        raw = mdx_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", posix_path, exc)
        return

    frontmatter, content = _split_frontmatter(raw)

    # Only exclude from index if parsing the frontmatter YAML fails.
    if frontmatter is None:
        # Use defaults — file is still valid.
        frontmatter = DocFrontmatter()
    elif isinstance(frontmatter, str):
        # YAML parse error — exclude this page.
        invalid[posix_path] = frontmatter
        logger.warning("Invalid frontmatter in %s: %s", posix_path, frontmatter)
        return

    if posix_path in pages:
        logger.warning("Duplicate path %s — keeping first occurrence", posix_path)
        return

    pages[posix_path] = DocPage(
        path=posix_path,
        frontmatter=frontmatter,
        content=content,
    )


def _split_frontmatter(raw: str) -> tuple[DocFrontmatter | str | None, str]:
    """Split ``---``-delimited YAML frontmatter from body content.

    Returns:
        A ``(frontmatter, content)`` tuple where *frontmatter* is:

        * A :class:`DocFrontmatter` on success.
        * ``None`` if no frontmatter fence is present.
        * A ``str`` error message when YAML parsing fails.
    """
    if not raw.startswith("---"):
        return None, raw

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None, raw

    yaml_text = parts[1].strip()
    content = parts[2].strip()

    # Empty frontmatter block → use defaults.
    if not yaml_text:
        return DocFrontmatter(), content

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return f"YAML error: {exc}", content

    if not isinstance(data, dict):
        return "Frontmatter is not a YAML mapping", content

    try:
        fm = DocFrontmatter.model_validate(data)
    except Exception as exc:
        return f"Frontmatter validation failed: {exc}", content

    return fm, content


def _normalise_path(path: str) -> str:
    """Normalise a requested path and reject path-traversal attempts.

    Strips leading ``/``, collapses ``..``, and ensures POSIX separators.
    """
    clean = path.replace("\\", "/").lstrip("/")
    segments = [s for s in clean.split("/") if s not in ("", ".")]
    if ".." in segments:
        raise PageNotFound(f"Path traversal rejected: {path!r}")
    return "/".join(segments)
