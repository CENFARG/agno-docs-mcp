"""Pydantic models for agno-docs-mcp.

All tool I/O and domain types are defined here as a single source of truth.
FastMCP integrates with Pydantic directly for JSON schema generation.
"""

from pydantic import BaseModel, DirectoryPath, Field


# ---- Domain models ----


class DocFrontmatter(BaseModel):
    """Metadata extracted from MDX YAML frontmatter.

    Attributes:
        title: Page title. Defaults to empty string when frontmatter is missing.
        description: Optional short description of the page.
        keywords: List of search keywords. Defaults to empty list.
    """

    title: str = ""
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class DocPage(BaseModel):
    """A single documentation page with parsed frontmatter and raw body content.

    Attributes:
        path: POSIX path relative to the docs root.
        frontmatter: Parsed DocFrontmatter.
        content: Raw markdown/MDX body (after frontmatter fence).
    """

    path: str
    frontmatter: DocFrontmatter
    content: str


class IndexDocument(BaseModel):
    """Payload fed to SearchEngine.index() for FTS5 insertion.

    Attributes:
        path: POSIX page path (stored UNINDEXED for payload retrieval).
        title: Page title (indexed).
        description: Optional description (stored UNINDEXED per FTS5 schema).
        content: Raw body text (indexed).
        keywords: Search keywords (indexed).
    """

    path: str
    title: str
    description: str | None = None
    content: str
    keywords: list[str] = Field(default_factory=list)


class SearchHit(BaseModel):
    """A single search result from the engine.

    Attributes:
        path: Page path.
        title: Page title.
        snippet: HTML-wrapped snippet with ``<b>`` markers around matches.
        score: BM25 relevance score (lower is more relevant).
    """

    path: str
    title: str
    snippet: str
    score: float


class DocHit(SearchHit):
    """Tool output alias for :class:`SearchHit`.

    Exists so tool signatures are self-documenting; identical to SearchHit.
    """


class NavNode(BaseModel):
    """A node in the navigation tree (recursive).

    Attributes:
        title: Display label.
        path: Page path or ``None`` for folder nodes.
        children: Sub-nodes. Defaults to empty list for leaf nodes.
    """

    title: str
    path: str | None = None
    children: list["NavNode"] = Field(default_factory=list)


class NavTree(BaseModel):
    """Navigation tree root wrapping a single :class:`NavNode`.

    Attributes:
        root: The root navigation node.
    """

    root: NavNode


# ---- Tool input schemas ----


class SearchDocsInput(BaseModel):
    """Input for the ``search_docs`` tool.

    Attributes:
        query: Search query string (minimum 2 characters).
        topic: Optional topic filter matched against ``keywords`` column.
        limit: Maximum results (1–50, default 10).
    """

    query: str = Field(min_length=2)
    topic: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)


class SearchExamplesInput(BaseModel):
    """Input for the ``search_examples`` tool.

    Attributes:
        query: Search query string (minimum 2 characters).
        limit: Maximum results (1–50, default 10).
    """

    query: str = Field(min_length=2)
    limit: int = Field(default=10, ge=1, le=50)


class GetPageInput(BaseModel):
    """Input for the ``get_page`` tool.

    Attributes:
        path: Relative page path (e.g. ``"api/agents.mdx"``).
    """

    path: str


# ---- Configuration models ----


class LocalSourceConfig(BaseModel):
    """Configuration for :class:`LocalMDXSource`.

    Attributes:
        root_path: Filesystem directory containing ``.mdx`` files and ``docs.json``.
    """

    root_path: DirectoryPath


class FTS5Config(BaseModel):
    """Configuration for :class:`FTS5Engine`.

    Attributes:
        db_path: Path for file-based SQLite database (``None`` = ``:memory:``).
        tokenizer: FTS5 tokenizer name (e.g. ``"porter"``, ``"unicode61"``).
        snippet_fragments: Max number of snippet fragments to return.
        snippet_tokens: Max tokens per snippet fragment.
    """

    db_path: str | None = None
    tokenizer: str = "porter"
    snippet_fragments: int = 3
    snippet_tokens: int = 12
