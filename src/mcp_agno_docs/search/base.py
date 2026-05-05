"""Abstract base class for search engines.

Defines the port that all search engine adapters must implement.
"""

from abc import ABC, abstractmethod

from mcp_agno_docs.models import IndexDocument, SearchHit


class SearchEngine(ABC):
    """Abstract port for full-text indexing and search.

    Concrete adapters (e.g., :class:`FTS5Engine`) implement indexing and
    querying against a specific backend. Tools depend on this ABC, never on
    concrete adapters or I/O details.

    Subclasses MUST implement :meth:`index` and :meth:`search`.
    :meth:`close` provides a default no-op.
    """

    @abstractmethod
    async def index(self, documents: list[IndexDocument]) -> None:
        """Index a batch of documents for later search.

        Args:
            documents: List of :class:`IndexDocument` payloads produced
                by a :class:`DocSource`.
        """
        ...

    @abstractmethod
    async def search(
        self, query: str, topic: str | None = None, limit: int = 10
    ) -> list[SearchHit]:
        """Execute a full-text search and return ranked hits.

        Args:
            query: Free-text search query.
            topic: Optional topic filter (matched against keywords).
            limit: Maximum number of hits to return.

        Returns:
            List of :class:`SearchHit` ordered by relevance (ascending
            score = more relevant).
        """
        ...

    async def close(self) -> None:
        """Release resources held by the engine (default no-op).

        Override in adapters that own a connection or file handle.
        """
