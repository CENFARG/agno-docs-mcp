"""Abstract base class for documentation sources.

Defines the port that all doc source adapters must implement.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from mcp_agno_docs.models import DocPage, IndexDocument


class DocSource(ABC):
    """Abstract port for loading and accessing documentation pages.

    Concrete adapters (e.g., :class:`LocalMDXSource`) implement loading
    from a specific storage backend. Tools depend on this ABC, never on
    concrete adapters or I/O details.

    Subclasses MUST implement all four abstract methods.
    """

    @abstractmethod
    async def load(self) -> None:
        """Preload and parse all documentation pages from the backend.

        Must be called once before ``get_page``, ``list_pages``, or
        ``iter_index_documents``. Blocking I/O implementations SHOULD
        wrap disk/network work in :func:`asyncio.to_thread`.
        """
        ...

    @abstractmethod
    def get_page(self, path: str) -> DocPage:
        """Retrieve a single page by its relative POSIX path.

        Args:
            path: Normalised POSIX path relative to the docs root
                (e.g. ``"api/agents.mdx"``).

        Returns:
            The matching :class:`DocPage`.

        Raises:
            PageNotFound: If *path* is not present in the loaded pages.
            PageInvalid: If the page exists but failed validation.
        """
        ...

    @abstractmethod
    def list_pages(self) -> list[str]:
        """Return every known page path (relative, POSIX-normalised).

        Returns:
            Sorted list of path strings.
        """
        ...

    @abstractmethod
    def iter_index_documents(self) -> Iterable[IndexDocument]:
        """Iterate over :class:`IndexDocument` payloads for search indexing.

        Yields:
            One :class:`IndexDocument` per loaded page, ready to be
            passed to :meth:`SearchEngine.index`.
        """
        ...
