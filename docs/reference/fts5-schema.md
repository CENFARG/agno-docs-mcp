# FTS5 Schema Reference

The SQLite FTS5 schema that powers agno-docs-mcp's search.

## Virtual Table Definition

```sql
CREATE VIRTUAL TABLE docs USING fts5(
    path,
    title,
    description,
    keywords,
    content,
    topic,                    -- extracted from keywords[0] for column filtering
    tokenize='porter unicode61'
);
```

## Column Map

| Column | Source | Tokenized? | Searchable? | Description |
|--------|--------|-----------|-------------|-------------|
| `path` | File path relative to docs root | No | No | Identifier, returned in results |
| `title` | YAML frontmatter `title` | Yes | Yes | Page title, used in ranking |
| `description` | YAML frontmatter `description` | Yes | Yes | Summary, used in ranking |
| `keywords` | YAML frontmatter `keywords` | Yes | Yes | Tags as comma-separated string |
| `content` | Full page body (markdown) | Yes | Yes | Primary search target |
| `topic` | `keywords[0]` or `""` | No | Column filter only | Powers `search_docs(topic=...)` |

## Tokenizer Configuration

```sql
tokenize='porter unicode61'
```

### Porter Stemmer

Reduces words to their root form:

| Input | Stem |
|-------|------|
| `running` | `run` |
| `agents` | `agent` |
| `connections` | `connect` |
| `streaming` | `stream` |


Queries are **also** stemmed before matching — so searching for `"agents"` matches documents containing `agent`, and vice versa.

### Unicode61

Handles Unicode text (diacritics removed, case-folded). Essential for the Agno docs which contain code examples with non-ASCII characters (emojis, Unicode symbols).

## BM25 Ranking

The ranking function (custom implementation):

```
BM25(d, q) = Σ IDF(q_i) · TF_norm(q_i, d)

Where:
  IDF(q_i)      = ln((N - n(q_i) + 0.5) / (n(q_i) + 0.5) + 1)
  TF_norm(q_i,d) = f(q_i, d) / (f(q_i, d) + avgdl / |d|)
```

SQL implementation (simplified):

```sql
SELECT
    path,
    title,
    snippet(content, 1, '<b>', '</b>', '...', 32) AS snippet,
    rank
FROM docs
WHERE docs MATCH :query
ORDER BY rank
LIMIT :limit
```

### Why Negative Scores

FTS5's `rank` column returns values where "more relevant" = lower number. The MCP protocol sorts results ascending by score, so negative values put the best results first.

A result with `-7.46` is **more relevant** than one with `-2.10`.

## Search Query Construction

### Basic Search (`search_docs`)

```sql
SELECT path, title, snippet(content, 1, '<b>', '</b>', '...', 32), rank
FROM docs
WHERE docs MATCH ?
ORDER BY rank
LIMIT ?
```

The query string is sanitized before being passed to `MATCH` — special FTS5 operators (`AND`, `OR`, `NOT`, `NEAR`) are escaped.

### Topic-Filtered Search

```sql
SELECT path, title, snippet(content, 1, '<b>', '</b>', '...', 32), rank
FROM docs
WHERE docs MATCH ?
  AND topic = ?           -- column filter
ORDER BY rank
LIMIT ?
```

The `topic` column filter is a **column constraint** — FTS5 evaluates it efficiently because `topic` is indexed as part of the virtual table.

### Example Search (`search_examples`)

```sql
-- Step 1: Fetch 4× the limit
SELECT path, title, snippet(content, 1, '<b>', '</b>', '...', 32), rank
FROM docs
WHERE docs MATCH ?
ORDER BY rank
LIMIT ?

-- Step 2: Post-filter in Python
results = [r for r in raw_results if r.path.startswith("examples/")]
results = results[:original_limit]
```

Over-fetching (4×) compensates for the scope restriction — only ~47% of pages are in `examples/`.

## Index Lifecycle

```
STARTUP:
  CREATE VIRTUAL TABLE docs (...)
  → FOR each .mdx file:
      INSERT INTO docs (path, title, ..., content) VALUES (...)

RUNTIME:
  SELECT ... FROM docs WHERE docs MATCH ?  ← Read-only

SHUTDOWN:
  DROP TABLE IF EXISTS docs  ← All data is in-memory, nothing persists
```

The index is **rebuild from scratch** on every server start. There is no persistence. This is intentional:

- Eliminates staleness (the Agno docs update frequently)
- Startup is fast (~2 seconds for 3,826 files)
- No cleanup logic needed
- No disk usage beyond the source `.mdx` files

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Index build (3,826 files) | ~2s | Disk read + FTS5 insert |
| `search_docs` (typical) | <5ms | In-memory SQLite, no I/O |
| `search_docs` (worst case) | ~50ms | Very common terms, large result set |
| `search_examples` | ~10ms | Same as search + Python post-filter |
| Memory usage | ~50MB | All content + FTS5 structures in RAM |
