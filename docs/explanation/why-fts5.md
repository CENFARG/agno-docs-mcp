# Why FTS5?

SQLite FTS5 was chosen as the search engine over alternatives. Here is the reasoning.

## The Problem

agno-docs-mcp needs to search 3,800+ documentation pages and return ranked, relevant results — fast. The search engine must:

1. **Run locally** — zero infrastructure, zero setup
2. **Rank well** — BM25 is the gold standard for keyword relevance
3. **Be fast** — sub-5ms queries on 3,800 documents
4. **Stem terms** — `agent` must match `agents`
5. **Support snippets** — show context around matched terms
6. **Be embeddable** — ship as a Python package, no external services

## Candidates Evaluated

| Engine | Ranking | Stemming | Embedded | Speed | Python API |
|--------|---------|----------|----------|-------|------------|
| **SQLite FTS5** | BM25 | Porter | ✅ Yes | ⚡ 3-5ms | ✅ sqlite3 |
| Whoosh | BM25 | Porter | ✅ Yes | 🐢 50-200ms | ✅ pip |
| Tantivy | BM25 | 17 langs | ✅ Yes | ⚡ 1-3ms | ❌ Rust FFI |
| Meilisearch | Custom | 17 langs | ❌ Needs server | ⚡ Fast | ✅ HTTP |
| Elasticsearch | BM25 | 40+ langs | ❌ Needs cluster | ⚡ Fast | ✅ HTTP |

## Why Not Each Alternative

### Whoosh

- **Pure Python**, no dependencies — appealing
- **Too slow** for 3,800 docs: 50-200ms per query
- Stale project (last release 2016, Python 2/3 port incomplete)
- A 200ms search adds up when an LLM makes 5-10 calls per response

### Tantivy

- **Rust-native**, blazing fast (1-3ms), excellent BM25
- Requires a Rust build chain or pre-compiled wheels
- Python bindings (`tantivy-py`) are immature and breaking-changes-heavy
- "Works on my machine" risk is high — distribution pain is real

### Meilisearch / Elasticsearch

- **Feature-rich**, professional-grade search
- Require a separate server process — violates "zero infrastructure"
- Network latency adds 5-10ms even on localhost
- Overkill for a single-user local tool

## Why FTS5 Wins

### 1. Ships with Python

SQLite is in Python's standard library. No `pip install`, no platform-specific builds, no Docker. It just works on Linux, macOS, and Windows — today.

### 2. Fast Enough

On 3,826 documents:

- Index build: ~2 seconds (startup, one-time)
- Query: 3-5ms (runtime, every call)
- 3ms × 10 tool calls = 30ms of search — invisible to the end user

### 3. BM25 Built-In

FTS5 provides BM25 via the `rank` column. The formula is battle-tested across decades of information retrieval research. No custom ranking code needed.

### 4. Porter Stemmer

The Porter stemmer is mature and predictable:

- `agent` ↔ `agents` ✅
- `connect` ↔ `connection` ✅
- `stream` ↔ `streaming` ✅
- False positives are rare

### 5. In-Memory, Ephemeral

The FTS5 database lives in `:memory:` — no files to clean up, no stale indexes. Every restart rebuilds from the source files, guaranteeing freshness.

## Tradeoffs Accepted

| Tradeoff | Mitigation |
|----------|-----------|
| No phrase queries | Quotes in search terms are stripped — the stemmer handles joins manually |
| No typo tolerance (fuzzy) | Users are searching docs, not user-generated text — exact-ish terms dominate |
| No semantic search (embeddings) | v0.5.0 roadmap; FTS5 is the MVP foundation |
| No persistence (rebuilds on start) | 2s startup is acceptable for a local dev tool |
| Single-language stemming | Agno docs are English-only |

## When We'd Switch

If any of these become true, we re-evaluate:

- **Non-English docs** added → need multi-language stemming
- **1M+ docs** → SQLite might slow down; consider Tantivy
- **Embedding models become trivial** → hybrid BM25 + vector (v0.5.0)
- **Remote server mode** → SSE transport changes deployment model; might prefer Meilisearch

## Bottom Line

FTS5 is the **right tool for the right job at the right time**. It's fast, zero-dependency, and does one thing exceptionally well: keyword search with relevance ranking. When the job outgrows it, the hexagonal architecture makes swapping engines a single-adapter change.
