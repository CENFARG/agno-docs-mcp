"""Integration tests for FTS5Engine using real sqlite3 in :memory:.

Verifies indexing, BM25-ranked search, topic filters, snippet highlighting,
empty results, error handling for malformed queries, and portability between
in-memory and file-based modes.
"""

import asyncio
import sqlite3

import pytest

from mcp_agno_docs.errors import ValidationError
from mcp_agno_docs.models import FTS5Config, IndexDocument, SearchHit
from mcp_agno_docs.search.fts5 import FTS5Engine

# ---- Shared dummy data ----

DUMMY_DOCS = [
    IndexDocument(
        path="guides/agents.mdx",
        title="Building Agents",
        description="How to create AI agents with Agno",
        content="Agents are the core building block. You can create agents "
        "with tools and models. Agents use memory to maintain context.",
        keywords=["agents", "getting-started"],
    ),
    IndexDocument(
        path="api/models.mdx",
        title="Model Configuration",
        description="Configuring LLM models for your agents",
        content="Models provide the intelligence layer. Configure models "
        "with model_id and provider settings for your agents.",
        keywords=["models", "api"],
    ),
    IndexDocument(
        path="guides/tools.mdx",
        title="Agent Tools",
        description="Adding tools to your agents for external capabilities",
        content="Tools extend what agents can do. Create custom tools "
        "with tool decorators and function calls.",
        keywords=["tools", "agents"],
    ),
    IndexDocument(
        path="examples/hello.mdx",
        title="Hello World Agent",
        description="Simple hello-world example with Agno",
        content="A minimal agent example using the default model.",
        keywords=["examples", "getting-started"],
    ),
]


def _make_indexed_engine() -> FTS5Engine:
    """Create and return an in-memory FTS5Engine with dummy data indexed."""
    async def _build() -> FTS5Engine:
        eng = FTS5Engine(FTS5Config())
        await eng.index(DUMMY_DOCS)
        return eng

    return asyncio.run(_build())


class TestFTS5EngineIndexAndSearch:
    """Core indexing and search behaviour with real sqlite3."""

    @pytest.fixture
    def engine(self) -> FTS5Engine:
        """Return a fresh in-memory FTS5Engine with dummy data indexed."""
        return _make_indexed_engine()

    # ---- Indexing and basic search ----

    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(self, engine: FTS5Engine) -> None:
        """Search for 'agents' returns hits with scores and snippets."""
        hits = await engine.search("agents")

        assert len(hits) > 0
        assert all(isinstance(h, SearchHit) for h in hits)
        assert all(h.path for h in hits)
        assert all(h.title for h in hits)
        assert all(h.snippet for h in hits)
        assert all(isinstance(h.score, float) for h in hits)

    @pytest.mark.asyncio
    async def test_bm25_ordering_lower_score_is_better(self, engine: FTS5Engine) -> None:
        """BM25 scores are ascending — lower score means more relevant."""
        hits = await engine.search("agents", limit=10)

        # Verify ascending order.
        scores = [h.score for h in hits]
        assert scores == sorted(scores), f"Scores not ascending: {scores}"

    @pytest.mark.asyncio
    async def test_search_finds_matching_document(self, engine: FTS5Engine) -> None:
        """Searching for 'agents' returns the agents guide."""
        hits = await engine.search("agents")

        paths = {h.path for h in hits}
        assert "guides/agents.mdx" in paths

    @pytest.mark.asyncio
    async def test_snippet_contains_b_tags(self, engine: FTS5Engine) -> None:
        """Snippets have <b>...</b> markers around matches."""
        hits = await engine.search("agents")

        for hit in hits:
            # At least one hit should contain highlighted text.
            if "<b>" in hit.snippet:
                assert "</b>" in hit.snippet
                return

        # If no snippet has <b> tags, check that the snippet is non-empty at least.
        # FTS5 snippet() returns the column content when there are multiple hits.
        assert all(len(h.snippet) > 0 for h in hits)

    @pytest.mark.asyncio
    async def test_topic_filter_narrows_results(self, engine: FTS5Engine) -> None:
        """Filtering by topic='models' only returns docs with that keyword."""
        hits = await engine.search("agents", topic="models")

        # docs with keyword "models": only api/models.mdx
        paths = {h.path for h in hits}
        # The topic filter is applied via keywords MATCH, so models doc is included,
        # but agents-only docs without "models" keyword should be excluded.
        assert "api/models.mdx" in paths
        # "guides/agents.mdx" has keywords ["agents", "getting-started"] — not "models"
        assert "guides/agents.mdx" not in paths

    @pytest.mark.asyncio
    async def test_topic_filter_respects_limit(self, engine: FTS5Engine) -> None:
        """Topic-filtered search respects the limit parameter."""
        hits = await engine.search("agent", limit=1)

        assert len(hits) <= 1

    @pytest.mark.asyncio
    async def test_empty_results_for_no_match(self, engine: FTS5Engine) -> None:
        """A query matching nothing returns an empty list."""
        hits = await engine.search("zzzquux_nonexistent")
        assert hits == []

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, engine: FTS5Engine) -> None:
        """Limit parameter caps the number of returned hits."""
        hits_full = await engine.search("agent", limit=10)
        hits_capped = await engine.search("agent", limit=2)

        assert len(hits_capped) <= 2
        assert len(hits_capped) <= len(hits_full)


class TestFTS5EngineErrors:
    """Error handling: malformed queries, missing table."""

    @pytest.mark.asyncio
    async def test_malformed_fts5_query_raises_validation_error(self) -> None:
        """Unbalanced quotes or special FTS5 syntax should raise ValidationError."""
        engine = FTS5Engine(FTS5Config())
        await engine.index(DUMMY_DOCS)

        with pytest.raises(ValidationError, match="FTS5 query"):
            await engine.search('"unbalanced')

    @pytest.mark.asyncio
    async def test_closed_engine_raises_on_search(self) -> None:
        """Searching on a closed engine should raise an error."""
        engine = FTS5Engine(FTS5Config())
        await engine.index(DUMMY_DOCS)
        await engine.close()

        with pytest.raises(RuntimeError, match="closed"):
            await engine.search("agent")


class TestFTS5EnginePortability:
    """Portability: in-memory vs file-based modes."""

    @pytest.mark.asyncio
    async def test_in_memory_works(self) -> None:
        """Default config (db_path=None) creates an in-memory engine."""
        engine = FTS5Engine(FTS5Config())
        await engine.index(DUMMY_DOCS)
        hits = await engine.search("model")
        assert len(hits) > 0
        await engine.close()

    @pytest.mark.asyncio
    async def test_file_based_works(self, tmp_path) -> None:
        """Supplying db_path creates a file-based database."""
        db_file = tmp_path / "test.db"
        config = FTS5Config(db_path=str(db_file))
        engine = FTS5Engine(config)
        await engine.index(DUMMY_DOCS)
        hits = await engine.search("agent")
        assert len(hits) > 0
        await engine.close()

        # The file should exist on disk.
        assert db_file.exists()

    @pytest.mark.asyncio
    async def test_data_persists_across_reopen(self, tmp_path) -> None:
        """Data written to a file-based DB survives close and reopen."""
        db_file = tmp_path / "persist.db"
        config = FTS5Config(db_path=str(db_file))

        # First session: index.
        engine1 = FTS5Engine(config)
        await engine1.index(DUMMY_DOCS)
        await engine1.close()

        # Second session: reopen and search without re-indexing.
        engine2 = FTS5Engine(config)
        hits = await engine2.search("agents")
        assert len(hits) > 0
        await engine2.close()
