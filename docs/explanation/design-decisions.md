# Design Decisions

Key design decisions made during agno-docs-mcp development and their rationale.

## Decision Log

### 1. In-Memory FTS5 (not persistent)

**Chosen**: FTS5 database in `:memory:`, rebuilt on every start.

**Rejected**: Persistent SQLite file on disk.

**Why**: The Agno docs update daily. A persistent index would be stale within hours. Rebuilding takes <2 seconds — faster than checking timestamps on 3,800 files. And no cleanup logic.

**Tradeoff**: 2-second startup vs. instant startup + staleness risk. For a local dev tool, freshness wins.

### 2. Porter Stemmer (not unicode61)

**Chosen**: `tokenize='porter unicode61'`.

**Rejected**: `tokenize='unicode61'` only (no stemming).

**Why**: Without stemming, `agent` would not match `agents`. The Agno docs use both forms interchangeably. Porter is mature (1980) and predictable — false positives are rare in English technical documentation.

**Tradeoff**: Slight over-stemming (`running` → `run` might match `runtime`) vs. missed matches. Over-matching is less harmful than under-matching for documentation search.

### 3. Custom BM25 (not FTS5 default)

**Chosen**: Custom BM25 implementation over FTS5's built-in `bm25()`.

**Why**: FTS5's `bm25()` function is documented but not available on all SQLite builds (it requires compile-time option `SQLITE_ENABLE_FTS5`). We can't control the user's SQLite distribution. The custom implementation is 15 lines of SQL and Python — simple, portable, and gives identical results.

### 4. Negative Scores

**Chosen**: BM25 scores are negative (e.g., `-7.46` is better than `-2.10`).

**Rejected**: Normalized positive scores (0–1).

**Why**: The MCP protocol sorts tool results by score ascending. FTS5 `rank` returns lower = better. Rather than transform scores (adding latency and losing precision), we let the protocol do what it already does. The negative values are an implementation detail — LLMs interpret them correctly when told "lower is better".

### 5. Python 3.11+ Minimum

**Chosen**: Requires Python 3.11.

**Rejected**: Python 3.9 or 3.10 support.

**Why**: Python 3.11 added significant performance improvements (10-60% faster). It's also the minimum version supported by `mcp>=1.0`. Supporting 3.9 would mean maintaining compatibility shims for `asyncio` improvements and type annotation syntax — complexity with no user benefit (3.9 reaches end-of-life October 2025).

### 6. No Page-Level Caching

**Chosen**: Pages are read from disk on every `get_page` call.

**Rejected**: LRU cache of parsed pages in memory.

**Why**: An LLM typically reads 1-5 pages per response. Disk reads are <1ms for a `.mdx` file. Caching would save sub-milliseconds while adding cache invalidation complexity. Not worth it until remote adapters (where latency is 50-200ms).

**Exception**: The navigation tree IS cached — parsing `docs.json` on every call would be wasteful.

### 7. Over-Fetching for `search_examples`

**Chosen**: Fetch `limit * 4` from FTS5, then post-filter by path.

**Rejected**: FTS5 path-prefix query (e.g., `MATCH '...' AND path:examples/*`).

**Why**: FTS5 doesn't support prefix matching in column filters natively. We could store `"examples/"` as a separate column, but that duplicates indexing data. Over-fetching is simpler: FTS5 is fast, the extra results are cheap, and the Python post-filter is trivial.

### 8. stdio Transport Only (v0.1.0)

**Chosen**: stdio transport exclusively.

**Rejected**: SSE or HTTP transport in v0.1.

**Why**: stdio is the MCP default — all clients support it. It requires zero network configuration, zero authentication, zero ports. SSE transport (v0.4.0 roadmap) enables remote access but introduces security concerns that need careful design.

### 9. Google-Style Docstrings

**Chosen**: Google-style docstrings for all public API.

**Rejected**: NumPy-style or Sphinx-style.

**Why**: Google-style is the most readable in plain text and renders well in both IDE hover tips and MkDocs Material. The project uses it consistently across all modules.

Example:

```python
def search_docs(
    query: str,
    topic: str | None = None,
    limit: int = 10,
) -> list[DocHit]:
    """Full-text search with BM25 ranking.

    Args:
        query: Search query string.
        topic: Optional keyword filter from page frontmatter.
        limit: Maximum results to return (1-50).

    Returns:
        Ranked list of matching documentation pages.
    """
```

### 10. Apache 2.0 License

**Chosen**: Apache 2.0.

**Rejected**: MIT, GPLv3, AGPLv3.

**Why**: Apache 2.0 provides explicit patent grant — important for an MCP tool that could be used in commercial AI products. It is more protective than MIT (no patent grant) while being less restrictive than GPL (no copyleft). Industry standard for MCP ecosystem.
