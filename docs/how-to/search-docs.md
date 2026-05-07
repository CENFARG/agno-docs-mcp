# How to Search Documentation

Use `search_docs` to find relevant documentation pages by keyword.

## Basic Search

Call `search_docs` with a search query:

**Tool signature:**

```
search_docs(query: str, topic?: str, limit?: int) → list[DocHit]
```

**What you get back:**

```json
[
  {
    "path": "examples/tools/mcp/overview.mdx",
    "title": "MCP Tools Overview",
    "score": -7.46,
    "snippet": "Use <b>MCP</b> to integrate <b>agent</b> <b>tools</b> with external systems..."
  },
  {
    "path": "cookbook/tools/mcp.mdx",
    "title": "MCP Integration",
    "score": -7.38,
    "snippet": "Connect your <b>agent</b> to external services via the <b>MCP</b> protocol..."
  }
]
```

**Key details:**

- **Lower score = more relevant** — BM25 ranking: -7.46 is more relevant than -7.38
- **`<b>` tags** mark matched terms in the snippet
- Results default to **10** items, override with `limit`

## Filter by Topic

Narrow results using the `topic` parameter:

```
search_docs("tool", topic="mcp")
```

Topics are matched against the `keywords` field in each page's YAML frontmatter. If a page's frontmatter is:

```yaml
---
title: MCP Overview
keywords: ["mcp", "tools", "integration"]
---
```

Then `topic="mcp"` will include it; `topic="agents"` will not.

## Search Only Examples

Use `search_examples` for code-focused searches:

```
search_examples(query: str, limit?: int) → list[DocHit]
```

This scopes the search to the `examples/` directory (1,797 pages), filtering out tutorials, cookbooks, and reference content. Perfect for finding code samples.

Internally, it fetches **4× the limit** from FTS5 and post-filters by path prefix to compensate for the scope constraint.

## Understanding BM25 Scores

BM25 (Best Match 25) is a probabilistic ranking function. The score formula:

```
BM25(d, q) = Σ IDF(q_i) · (f(q_i, d) · (k1 + 1)) / (f(q_i, d) + k1 · (1 - b + b · |d|/avgdl))
```

**In plain terms:**

| Factor | Effect on score |
|--------|----------------|
| Term appears often in document | ↑ score (but saturates via k1) |
| Term is rare across all docs | ↑ score (IDF boost) |
| Document is long | ↓ score (length normalization) |
| Term matches exact form | ↑ score (Porter stemmer handles variants) |

Scores are **negative** because MCP's numeric sort is ascending, and we want "more relevant" at the top.

## Porter Stemming

The FTS5 index uses the Porter stemmer tokenizer. This means:

- `agent` matches `agents`, `agentic`, `agential`
- `connect` matches `connects`, `connected`, `connecting`, `connection`
- But NOT `MCP` → `mcps` (the stemmer doesn't handle acronyms)

Search for full words when possible; the stemmer handles the rest.

## Tips

- **Be specific**: `"MCP agent tools"` returns better results than `"tools"`
- **Use quotes** for exact phrases: `search_docs('"model context protocol"')`
- **Keep limits reasonable**: The default of 10 is usually enough; 50 max
- **Check snippets first**: Read `<b>`-highlighted context before fetching full pages
