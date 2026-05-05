"""Tests for the SearchEngine abstract base class.

Verifies that SearchEngine cannot be instantiated directly, that subclasses
MUST implement all abstract methods, and that close() provides a default
no-op implementation.
"""

import pytest

from mcp_agno_docs.models import IndexDocument, SearchHit
from mcp_agno_docs.search.base import SearchEngine


class TestSearchEngineContract:
    """SearchEngine ABC enforces its interface contract."""

    def test_cannot_instantiate_abc_directly(self) -> None:
        """Instantiating SearchEngine directly MUST raise TypeError."""
        with pytest.raises(TypeError, match="abstract"):
            SearchEngine()  # type: ignore[abstract]

    def test_subclass_without_index_fails_instantiation(self) -> None:
        """Missing async index() prevents instantiation."""

        class Incomplete(SearchEngine):
            async def search(
                self, query: str, topic: str | None = None, limit: int = 10
            ) -> list[SearchHit]:
                return []

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_subclass_without_search_fails_instantiation(self) -> None:
        """Missing async search() prevents instantiation."""

        class Incomplete(SearchEngine):
            async def index(self, documents: list[IndexDocument]) -> None:
                pass

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_fully_implemented_subclass_instantiates(self) -> None:
        """A subclass implementing both abstract methods instantiates successfully."""

        class Complete(SearchEngine):
            async def index(self, documents: list[IndexDocument]) -> None:
                pass

            async def search(
                self, query: str, topic: str | None = None, limit: int = 10
            ) -> list[SearchHit]:
                return []

        engine = Complete()
        assert isinstance(engine, SearchEngine)

    @pytest.mark.asyncio
    async def test_close_is_concrete_noop(self) -> None:
        """close() has a default async no-op implementation that does not raise."""

        class Minimal(SearchEngine):
            async def index(self, documents: list[IndexDocument]) -> None:
                pass

            async def search(
                self, query: str, topic: str | None = None, limit: int = 10
            ) -> list[SearchHit]:
                return []

        engine = Minimal()
        result = await engine.close()
        assert result is None
