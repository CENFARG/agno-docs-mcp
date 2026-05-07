"""Filesystem adapter that reads ``.mdx`` files from a local directory.

Walks a ``root_path`` recursively, parses YAML frontmatter from each
``.mdx`` file, and returns :class:`DocPage` objects. Implements the
:class:`DocSource` abstract port.

All blocking disk I/O is wrapped in :func:`asyncio.to_thread` so the
event loop is never blocked.
"""

import asyncio
import logging
from collections.abc import Iterator
from dataclasses import dataclass
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
from mcp_agno_docs.utils import normalise_path

logger = logging.getLogger(__name__)


@dataclass
class FileResult:
    """Result of processing a single ``.mdx`` file.

    Attributes:
        page: The parsed :class:`DocPage`, or ``None`` if the file was
            skipped, unreadable, or had invalid frontmatter.
        error: Error message when frontmatter parsing failed; ``None``
            on success or skip.
        path: POSIX-relative path of the processed file.
    """

    page: DocPage | None
    error: str | None
    path: str


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
                result = _process_file(mdx_file, self._root)
                if result.page is not None:
                    path = result.page.path
                    if path not in pages:
                        pages[path] = result.page
                    else:
                        logger.warning(
                            "Duplicate path %s — keeping first occurrence", path
                        )
                elif result.error is not None:
                    invalid[result.path] = result.error
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
            ValidationError: If *path* contains ``..`` (traversal attempt).
        """
        normalised = normalise_path(path)
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

    def iter_index_documents(self) -> Iterator[IndexDocument]:
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


def _process_file(mdx_file: Path, root: Path) -> FileResult:
    """Parse a single ``.mdx`` file and return a :class:`FileResult`.

    Args:
        mdx_file: Absolute path to the ``.mdx`` file.
        root: The docs root directory (for computing relative paths).

    Returns:
        A :class:`FileResult` with ``page`` set on success, ``error`` set
        on frontmatter failure, and both ``None`` when the file is skipped
        (hidden, unreadable, or non-existent).
    """
    # Skip hidden / dot-files.
    if mdx_file.name.startswith("."):
        return FileResult(page=None, error=None, path="")

    rel = mdx_file.relative_to(root)
    posix_path = rel.as_posix()

    try:
        raw = mdx_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", posix_path, exc)
        return FileResult(page=None, error=None, path=posix_path)

    try:
        frontmatter, content = _split_frontmatter(raw)
    except ValueError as exc:
        # YAML parse error — exclude this page.
        logger.warning("Invalid frontmatter in %s: %s", posix_path, exc)
        return FileResult(page=None, error=str(exc), path=posix_path)

    # Only exclude from index if parsing the frontmatter YAML fails.
    if frontmatter is None:
        # Use defaults — file is still valid.
        frontmatter = DocFrontmatter()

    page = DocPage(
        path=posix_path,
        frontmatter=frontmatter,
        content=content,
    )
    return FileResult(page=page, error=None, path=posix_path)


def _split_frontmatter(raw: str) -> tuple[DocFrontmatter | None, str]:
    """Split ``---``-delimited YAML frontmatter from body content.

    Returns:
        A ``(frontmatter, content)`` tuple where *frontmatter* is:

        * A :class:`DocFrontmatter` on success.
        * ``None`` if no frontmatter fence is present.

    Raises:
        ValueError: If YAML parsing fails or frontmatter is not a mapping.
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
        raise ValueError(f"YAML error: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Frontmatter is not a YAML mapping")

    try:
        fm = DocFrontmatter.model_validate(data)
    except Exception as exc:
        raise ValueError(f"Frontmatter validation failed: {exc}") from exc

    return fm, content
