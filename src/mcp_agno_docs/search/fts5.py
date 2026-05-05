"""FTS5 full-text search engine adapter.

Provides an in-memory (or file-based) SQLite FTS5 search backend that
implements the :class:`SearchEngine` abstract port. All blocking sqlite3
calls are wrapped in :func:`asyncio.to_thread`.
"""

import asyncio
import sqlite3

from mcp_agno_docs.errors import ValidationError
from mcp_agno_docs.models import FTS5Config, IndexDocument, SearchHit
from mcp_agno_docs.search.base import SearchEngine

# Column indices in the FTS5 virtual table (0-based).
COL_TITLE = 0
COL_DESCRIPTION = 1  # UNINDEXED
COL_CONTENT = 2
COL_PATH = 3  # UNINDEXED
COL_KEYWORDS = 4


class FTS5Engine(SearchEngine):
    """SQLite FTS5 adapter implementing the :class:`SearchEngine` port.

    Creates a virtual table ``docs`` with Porter stemming tokenizer.
    Supports both in-memory (``db_path=None``) and file-based persistence.

    Args:
        config: :class:`FTS5Config` with tokenizer, snippet options, and
            optional file path.
    """

    def __init__(self, config: FTS5Config) -> None:
        self._config = config
        self._db_path: str | None = config.db_path
        self._conn: sqlite3.Connection | None = None
        self._closed = False

    # ---- SearchEngine interface ----

    async def index(self, documents: list[IndexDocument]) -> None:
        """Batch-insert *documents* into the FTS5 virtual table.

        The entire batch runs inside a single ``BEGIN/COMMIT`` transaction
        for performance. The connection and virtual table are created
        lazily on first call.
        """
        if not documents:
            return

        def _run() -> None:
            conn = self._ensure_conn()
            rows = [
                (
                    d.title,
                    d.description or "",
                    d.content,
                    d.path,
                    " ".join(d.keywords),
                )
                for d in documents
            ]
            with conn:
                conn.executemany(
                    "INSERT INTO docs(title, description, content, path, keywords) "
                    "VALUES (?, ?, ?, ?, ?)",
                    rows,
                )

        await asyncio.to_thread(_run)

    async def search(
        self, query: str, topic: str | None = None, limit: int = 10
    ) -> list[SearchHit]:
        """Execute a BM25-ranked full-text search.

        Args:
            query: Free-text FTS5 MATCH expression.
            topic: Optional keyword filter (phrase-matched against the
                ``keywords`` column).
            limit: Maximum hits.

        Returns:
            Hits ordered by ascending BM25 score (lower = more relevant).

        Raises:
            ValidationError: If *query* contains malformed FTS5 syntax.
        """

        def _run() -> list[SearchHit]:
            conn = self._ensure_conn()
            tokens = self._config.snippet_tokens

            sql = (
                "SELECT path, title, "
                f"snippet(docs, {COL_CONTENT}, '<b>', '</b>', '...', {tokens}) "
                "AS snippet, "
                "bm25(docs) AS score "
                "FROM docs "
                "WHERE docs MATCH ?"
            )
            params: list = [query]

            if topic:
                sql += " AND keywords MATCH ?"
                params.append(f'"{topic}"')

            sql += " ORDER BY score LIMIT ?"
            params.append(limit)

            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError as exc:
                raise ValidationError(
                    f"FTS5 query error: {exc}"
                ) from exc

            return [
                SearchHit(
                    path=row[0],
                    title=row[1],
                    snippet=row[2],
                    score=row[3],
                )
                for row in rows
            ]

        return await asyncio.to_thread(_run)

    async def close(self) -> None:
        """Close the SQLite connection and mark the engine as closed."""

        def _run() -> None:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
            self._closed = True

        await asyncio.to_thread(_run)

    # ---- Internal helpers ----

    def _ensure_conn(self) -> sqlite3.Connection:
        """Return the sqlite3 connection, creating it and the schema lazily.

        Raises:
            RuntimeError: If the engine has been closed.
        """
        if self._closed:
            raise RuntimeError("Engine is closed")
        if self._conn is None:
            db = self._db_path if self._db_path else ":memory:"
            self._conn = sqlite3.connect(db, check_same_thread=False)
            self._create_schema()
        return self._conn

    def _create_schema(self) -> None:
        """Create the ``docs`` FTS5 virtual table with Porter stemming.

        Raises:
            RuntimeError: If table creation fails (engine left unusable).
        """
        assert self._conn is not None
        tokenizer = self._config.tokenizer
        try:
            self._conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5("
                f"title, description UNINDEXED, content, path UNINDEXED, "
                f"keywords, tokenize='{tokenizer}')"
            )
        except sqlite3.OperationalError as exc:
            raise RuntimeError(
                f"Failed to create FTS5 virtual table: {exc}"
            ) from exc
