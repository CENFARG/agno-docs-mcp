"""FastMCP server assembly and lifespan management.

Creates the FastMCP application, wires together ``DocSource`` +
``SearchEngine`` + ``NavTree`` during startup, and exposes a ``run``
entry-point for the CLI.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from mcp_agno_docs.indexer.navigation import load_navigation
from mcp_agno_docs.models import (
    FTS5Config,
    LocalSourceConfig,
    NavTree,
)
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.search.fts5 import FTS5Engine
from mcp_agno_docs.sources.base import DocSource
from mcp_agno_docs.sources.local_mdx import LocalMDXSource

# Import tools to trigger @mcp.tool() registration side-effects.
# These imports MUST come after the ``mcp`` instance is created in
# tools/__init__.py.
from mcp_agno_docs.tools import mcp  # noqa: F401 — FastMCP instance
import mcp_agno_docs.tools.navigation  # noqa: F401 — registers get_navigation
import mcp_agno_docs.tools.pages  # noqa: F401 — registers get_page
import mcp_agno_docs.tools.search  # noqa: F401 — registers search_docs, search_examples

logger = logging.getLogger(__name__)


class AppContext:
    """Application context injected into the FastMCP lifespan.

    Attributes:
        source: Loaded documentation source (e.g. :class:`LocalMDXSource`).
        engine: Indexed search engine (e.g. :class:`FTS5Engine`).
        nav: Pre-parsed navigation tree from ``docs.json``.
    """

    def __init__(self, source: DocSource, engine: SearchEngine, nav: NavTree) -> None:
        self.source = source
        self.engine = engine
        self.nav = nav


def run_server(docs_path: str | Path) -> None:
    """Start the MCP server on stdio transport.

    All blocking I/O during startup (disk reads, SQLite operations,
    JSON parsing) is wrapped in :func:`asyncio.to_thread` by the
    adapters.  The tools become available once the lifespan yields
    the :class:`AppContext`.

    Args:
        docs_path: Path to the Agno docs directory containing ``.mdx``
            files and ``docs.json``.
    """
    root = Path(docs_path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Docs path is not a directory: {root}")

    _configure_lifespan(root)

    # ``mcp.run()`` is synchronous and blocks on stdio.
    mcp.run(transport="stdio")


def _configure_lifespan(docs_root: Path) -> None:
    """Replace the default no-op lifespan with our startup/shutdown sequence.

    The lifespan is installed directly on the low-level ``_mcp_server``
    because ``FastMCP.lifespan`` is a constructor-only parameter.

    .. note::

        ``_mcp_server.lifespan`` is a known technical debt point.
        FastMCP does not currently expose a public API to replace the
        lifespan after construction. We use ``Any`` for the *server*
        parameter because the concrete type is a private FastMCP
        implementation detail not exported by the library.
    """

    @asynccontextmanager
    async def lifespan(server: Any) -> AsyncIterator[AppContext]:
        """Wire adapters, load docs, index, and serve.

        Args:
            server: FastMCP internal server instance (private API —
                typed as ``Any`` since FastMCP does not export it).
        """
        source = LocalMDXSource(LocalSourceConfig(root_path=docs_root))
        engine = FTS5Engine(FTS5Config())
        try:
            logger.info("Loading docs from %s ...", docs_root)
            await source.load()
            docs = list(source.iter_index_documents())
            logger.info("Indexing %d documents ...", len(docs))
            await engine.index(docs)
            logger.info("Loading navigation ...")
            nav = await asyncio.to_thread(
                load_navigation, docs_root / "docs.json"
            )
            logger.info("Startup complete — %d pages indexed.", len(docs))
            ctx = AppContext(source=source, engine=engine, nav=nav)
            yield ctx
        finally:
            logger.info("Shutting down ...")
            await engine.close()

    mcp._mcp_server.lifespan = lifespan
