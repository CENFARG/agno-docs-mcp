# Hexagonal Architecture

agno-docs-mcp uses hexagonal (ports and adapters) architecture. Here is why and how.

## What Is Hexagonal Architecture?

Also known as **Ports and Adapters**, it separates the application core from infrastructure:

```
┌──────────────────────────────────────────────┐
│                APPLICATION CORE               │
│  (tools, models, business logic — pure)       │
│                                               │
│    ┌──────────┐              ┌──────────┐     │
│    │ DocSource│              │SearchEng.│     │
│    │  (port)  │              │  (port)  │     │
│    └────┬─────┘              └────┬─────┘     │
│         │                         │           │
└─────────┼─────────────────────────┼───────────┘
          │                         │
    ┌─────┴─────┐             ┌─────┴─────┐
    │LocalMDX   │             │FTS5Engine │
    │(adapter)  │             │(adapter)  │
    └─────┬─────┘             └─────┬─────┘
          │                         │
    ┌─────┴─────┐             ┌─────┴─────┐
    │Filesystem │             │  SQLite   │
    └───────────┘             └───────────┘
```

The **ports** are abstract interfaces (ABCs). The **adapters** are concrete implementations. The application core depends ONLY on the ports — never on adapters.

## Why Hexagonal Here?

### Problem: Lock-in

Without ports, the tools would call SQLite and filesystem APIs directly:

```python
# ❌ Leaky — tool knows about SQLite
def search_docs(query: str):
    conn = sqlite3.connect(":memory:")
    cursor = conn.execute("SELECT ... FROM docs WHERE MATCH ?", [query])
    return [DocHit.from_row(row) for row in cursor]
```

Now what happens when we want to add vector search?

- Rewrite `search_docs`
- Rewrite `search_examples`
- Rewrite tests
- Hope nothing breaks

### Solution: Ports

With ports, the tool depends only on an abstraction:

```python
# ✅ Clean — tool knows nothing about implementation
async def search_docs(
    ctx: Context, query: str, topic: str | None = None, limit: int = 10
) -> list[DocHit]:
    app = ctx.request_context.lifespan_context
    return await app.search_engine.search(query, topic, limit)
```

To add vector search, implement a new adapter behind the same port. Zero tool changes.

## The Two Ports

### `DocSource` — "Where do pages come from?"

```python
class DocSource(ABC):
    async def get_page(self, path: str) -> DocPage: ...
    async def list_pages(self) -> list[str]: ...
    async def get_nav_tree(self) -> NavTree: ...
```

Today: `LocalMDXSource` reads from the filesystem.

Tomorrow: `RemoteDocSource` fetches from HTTP, `S3DocSource` from cloud storage, `GitDocSource` clones a repo. All implement the same three methods.

### `SearchEngine` — "How do we search?"

```python
class SearchEngine(ABC):
    async def index(self, pages: list[DocPage]) -> None: ...
    async def search(self, query: str, topic: str | None, limit: int) -> list[DocHit]: ...
    async def search_examples(self, query: str, limit: int) -> list[DocHit]: ...
```

Today: `FTS5Engine` uses SQLite FTS5.

Tomorrow: `VectorSearchEngine` uses embeddings, `MeilisearchEngine` uses Meilisearch, `HybridEngine` combines both.

## Dependency Injection

`AppContext` wires everything together:

```python
class AppContext:
    doc_source: DocSource
    search_engine: SearchEngine
    nav_tree: NavTree | None
```

At startup:

```python
# Wire the adapters
doc_source = LocalMDXSource(docs_path)
search_engine = FTS5Engine(tokenizer="porter")

# Load and index
pages = await doc_source.list_pages_full()
await search_engine.index(pages)

# Create context — this is what tools receive
app_ctx = AppContext(
    doc_source=doc_source,
    search_engine=search_engine,
    nav_tree=nav_tree
)
```

Tools receive `app_ctx` through FastMCP's lifespan context. They call `app_ctx.search_engine.search(...)` — never knowing whether it's SQLite, vectors, or Meilisearch.

## Testing Benefits

Mocking is trivial because ports are defined as ABCs:

```python
class MockSearchEngine(SearchEngine):
    async def search(self, query, topic, limit):
        return [DocHit(path="test.mdx", title="Test", score=-1.0, snippet="...")]

# Inject mock — no SQLite needed
app_ctx = AppContext(
    doc_source=MockDocSource(),
    search_engine=MockSearchEngine()
)
```

Unit tests never touch the filesystem or SQLite. They test **behavior**, not infrastructure.

## When NOT to Use Hexagonal

Hexagonal architecture adds abstraction cost:

- Two extra files (ports) for every adapter
- Indirection — "where does this method actually go?"
- Overkill for scripts and throwaway code

The rule: **use it when adapters are likely to change**. For agno-docs-mcp, the adapters are the whole point — FTS5 today, vectors tomorrow, remote next month. The architecture earns its keep on the second adapter.

## Real Example: Adding a New Adapter

To add `RemoteDocSource` (HTTP-based docs):

1. Create `src/mcp_agno_docs/sources/remote.py`:
   ```python
   class RemoteDocSource(DocSource):
       def __init__(self, base_url: str): ...
       async def get_page(self, path: str) -> DocPage:
           # Fetch from HTTP
   ```

2. Update startup wiring (one line):
   ```python
   doc_source = RemoteDocSource(base_url="https://api.agno.com/docs")
   ```

3. Done. Tools, tests (with new mocks), and models are untouched.

That is the power of ports and adapters.
