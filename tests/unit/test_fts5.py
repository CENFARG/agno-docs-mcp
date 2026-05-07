"""Tests for SearchEngine ABC, FTS5 helpers, and tokenizer validation.

Covers SearchEngine contract enforcement, _escape_fts_phrase escaping,
FTS5 tokenizer whitelist validation, and error-message sanitization.
"""

import asyncio

import pytest

from mcp_agno_docs.errors import ValidationError
from mcp_agno_docs.models import FTS5Config, IndexDocument, SearchHit
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.search.fts5 import _escape_fts_phrase, FTS5Engine  # noqa: F811


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


# ---- _escape_fts_phrase tests (C1 fix) ----

class TestEscapeFTSPhrase:
    """Unit tests for _escape_fts_phrase — FTS5 topic injection prevention."""

    def test_normal_topic_untouched(self) -> None:
        """A simple topic string is wrapped in double-quotes without change."""
        result = _escape_fts_phrase("getting-started")
        assert result == '"getting-started"'

    def test_topic_with_double_quotes_escaped(self) -> None:
        """Internal double-quotes are escaped by doubling them per FTS5 spec."""
        result = _escape_fts_phrase('hello"world')
        assert result == '"hello""world"'

    def test_topic_with_multiple_double_quotes(self) -> None:
        """Multiple double-quotes are each escaped independently."""
        result = _escape_fts_phrase('a"b"c')
        assert result == '"a""b""c"'

    def test_topic_with_only_double_quote(self) -> None:
        """A single double-quote alone is escaped correctly."""
        result = _escape_fts_phrase('"')
        assert result == '""""'

    def test_empty_topic_returns_quoted_empty(self) -> None:
        """Empty topic returns '""' (empty FTS5 phrase)."""
        result = _escape_fts_phrase("")
        assert result == '""'

    def test_topic_with_spaces_preserved(self) -> None:
        """Spaces inside topic are preserved, only quotes are escaped."""
        result = _escape_fts_phrase("api reference")
        assert result == '"api reference"'


# ---- Tokenizer validation tests (C3 fix) ----

class TestTokenizerValidation:
    """Unit tests for tokenizer whitelist validation in _create_schema."""

    def test_valid_tokenizer_porter_accepted(self) -> None:
        """The 'porter' tokenizer is in the whitelist and creates without error."""
        cfg = FTS5Config(tokenizer="porter")
        engine = FTS5Engine(cfg)
        # Access internal state to trigger schema creation.
        engine._ensure_conn()
        assert engine._conn is not None
        asyncio.run(engine.close())

    def test_valid_tokenizer_unicode61_accepted(self) -> None:
        """The 'unicode61' tokenizer is in the whitelist."""
        cfg = FTS5Config(tokenizer="unicode61")
        engine = FTS5Engine(cfg)
        engine._ensure_conn()
        assert engine._conn is not None
        asyncio.run(engine.close())

    def test_invalid_tokenizer_raises_valueerror(self) -> None:
        """An unknown tokenizer raises ValueError before DDL execution."""
        cfg = FTS5Config(tokenizer="malicious; DROP TABLE users;--")
        engine = FTS5Engine(cfg)
        with pytest.raises(ValueError, match="tokenizer"):
            engine._ensure_conn()

    def test_empty_tokenizer_raises_valueerror(self) -> None:
        """Empty tokenizer string is rejected."""
        cfg = FTS5Config(tokenizer="")
        engine = FTS5Engine(cfg)
        with pytest.raises(ValueError, match="tokenizer"):
            engine._ensure_conn()

    def test_ascii_tokenizer_accepted(self) -> None:
        """The 'ascii' tokenizer is in the whitelist."""
        cfg = FTS5Config(tokenizer="ascii")
        engine = FTS5Engine(cfg)
        engine._ensure_conn()
        assert engine._conn is not None
        asyncio.run(engine.close())
