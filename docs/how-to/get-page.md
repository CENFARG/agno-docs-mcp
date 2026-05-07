# How to Get a Page

Use `get_page` to retrieve the full content and metadata of a single documentation page.

## Retrieving a Page

Call `get_page` with the relative path from the docs root:

**Tool signature:**

```
get_page(path: str) → DocPage
```

**Example call:**

```
get_page("culture/overview.mdx")
```

**What you get back:**

```json
{
  "path": "culture/overview.mdx",
  "title": "What is Culture?",
  "description": "Learn about Agno's Culture system",
  "keywords": ["culture", "models", "prompts"],
  "content": "## What is Culture?\n\nCulture is the **personality** that you assign to your Agent...",
  "content_length": 11116
}
```

## Page Content Structure

The response includes two parts:

### Frontmatter (metadata)

Parsed from each page's YAML header:

```yaml
---
title: Getting Started
description: Quick start guide for Agno
keywords: ["getting-started", "installation", "setup"]
---
```

These fields become `title`, `description`, and `keywords` in the response.

### Body (content)

The raw markdown/MDX content, including:

- Code blocks (with language annotations)
- Callouts and admonitions
- Tables and diagrams
- Cross-references to other pages

## Finding a Page Path

Don't guess paths — use `search_docs` to discover what's available:

1. **Search** for the topic: `search_docs("streaming")`
2. **Note the path** from the result: `"cookbook/agents/streaming.mdx"`
3. **Fetch the full page**: `get_page("cookbook/agents/streaming.mdx")`

The path is always relative to the docs root and uses forward slashes.

## Common Patterns

### Read a page while coding

```
1. search_docs("async agent")  → find relevant pages
2. get_page("concepts/agents/async.mdx")  → read the most relevant one
3. Use the code samples in your implementation
```

### Verify a claim

```
1. search_docs("MCP transport")  → find authoritative source
2. get_page("cookbook/tools/mcp.mdx")  → read the full official doc
3. Confirm or refute based on official content
```

### Explore an API

```
1. get_navigation()  → browse the tree structure
2. Find the right section  → locate relevant paths
3. get_page(path)  → read the full API reference
```

## Limits

- **Content is read-only** — `get_page` returns content, it doesn't modify anything
- **No recursive fetch** — each call returns exactly one page
- **Large pages** — All content is in memory; there's no pagination for individual pages
- **Binary files** — Only `.mdx` files are supported; images and other assets are skipped

## Error Handling

If the page doesn't exist:

```
get_page("nonexistent/page.mdx")
→ Error: Page not found: nonexistent/page.mdx
```

If a page has no YAML frontmatter:

```
→ title defaults to the filename, description and keywords are empty
```
