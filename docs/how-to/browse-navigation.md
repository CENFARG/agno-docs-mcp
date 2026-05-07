# How to Browse the Navigation Tree

Use `get_navigation` to explore the full documentation structure.

## Getting the Navigation

**Tool signature:**

```
get_navigation() → NavTree
```

This returns the complete hierarchical structure from `docs.json` — no arguments needed.

## What You Get

The navigation is a tree of **tabs** containing **groups** containing **pages**:

```json
{
  "tabs": [
    {
      "label": "SDK",
      "groups": [
        {
          "label": "Getting Started",
          "pages": [
            {"path": "sdk/getting-started/overview.mdx", "label": "Overview"},
            {"path": "sdk/getting-started/installation.mdx", "label": "Installation"}
          ]
        },
        {
          "label": "Agents",
          "pages": [
            {"path": "sdk/agents/create.mdx", "label": "Create Agent"},
            {"path": "sdk/agents/configure.mdx", "label": "Configure Agent"}
          ]
        }
      ]
    },
    {
      "label": "Examples",
      "groups": [...]
    }
  ]
}
```

## Navigation Structure

The Agno docs ship with 7 top-level tabs:

| Tab | Content |
|-----|---------|
| Home | Landing page and overview |
| SDK | Core API reference |
| AgentOS | Agent orchestration platform |
| Deploy | Deployment guides |
| Examples | Code examples (1,797 pages) |
| Reference | Technical reference |
| FAQs | Frequently asked questions |

Each tab can have 1–20+ groups, and each group can have 1–100+ pages.

## In Your AI Coding Assistant

When connected to an MCP client, you can browse interactively:

```
You: What sections does the Agno docs have?
AI: [calls get_navigation, sees 7 tabs, reads their labels]
The docs have 7 sections: Home, SDK, AgentOS, Deploy, Examples, Reference, FAQs.

You: Show me the SDK Agents section.
AI: [calls get_navigation, drills into SDK → Agents group]
The SDK Agents section has:
- Create Agent
- Configure Agent
- Run Agent
- ...

You: Read the Create Agent page.
AI: [calls get_page("sdk/agents/create.mdx")]
Here's the full content...
```

## Tips

- **Start broad** — call `get_navigation` first to understand what's available
- **Drill down** — use the structure to guide which pages to fetch
- **Pair with search** — `search_docs` finds by topic; `get_navigation` finds by structure
- **The tree is cached** — `get_navigation` is instant after the first call

## Caching

The navigation tree is parsed from `docs.json` at startup and cached in `AppContext`. Subsequent calls to `get_navigation` return the cached tree — no disk I/O, near-zero latency.
