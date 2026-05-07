# How to Use the Topic Filter

The `topic` parameter in `search_docs` lets you narrow results to pages tagged with specific keywords.

## Basic Topic Filtering

When you call `search_docs` with a `topic`:

```
search_docs("tool", topic="mcp")
```

Only pages whose YAML frontmatter includes `"mcp"` in their `keywords` list are returned:

```yaml
---
title: MCP Tools
keywords: ["mcp", "tools", "integration"]  # ✅ matches topic="mcp"
---
```

```yaml
---
title: Agent Configuration
keywords: ["agents", "configuration"]  # ❌ won't match topic="mcp"
---
```

## How Topics Are Indexed

During indexing, each page's `keywords` are extracted from the YAML frontmatter and stored in the FTS5 index as a separate column. When you pass a `topic`, the engine adds a **column filter** to the FTS5 query:

```sql
SELECT path, title, snippet(content, 1, '<b>', '</b>', '...', 32)
FROM docs
WHERE docs MATCH 'tool'
  AND topic = 'mcp'            -- ← column filter
ORDER BY rank
LIMIT 10
```

This is **fast** — FTS5 column filters are indexed, not scanned.

## Finding Available Topics

There's no `list_topics` tool (yet). To discover what topics are available:

1. Call `get_navigation` — browse the tabs and groups
2. Search broadly without a topic filter
3. Use common Agno concepts as topics: `agents`, `tools`, `models`, `mcp`, `knowledge`, `workflows`, `teams`, `memory`

## Topic Filter Tips

- **Topic is case-sensitive** — `"MCP"` ≠ `"mcp"`. Use lowercase.
- **Exact match only** — `topic="agent"` won't match `"agents"`. Search for the singular form.
- **Combine with query** — topic narrows **which pages**; query narrows **within those pages**
- **Start without a topic** — use the default broad search first, then add a topic if results are too noisy

## When to Use a Topic Filter

| Scenario | Use topic? |
|----------|-----------|
| Learning about a specific feature | ✅ Yes — `topic="streaming"` |
| Broad exploration of the framework | ❌ No — leave empty, browse broadly |
| Finding code examples | ❌ No — use `search_examples` instead |
| Researching a concept | ✅ Yes — `topic="agents"` |
| Comparing approaches | ❌ No — see all relevant docs regardless of tag |
