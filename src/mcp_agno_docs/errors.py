"""Domain exceptions for agno-docs-mcp.

All exceptions inherit from :class:`Exception`. Translation to MCP error
types (ToolError, NotFound, etc.) happens at the tool boundary — engines
and sources never import MCP types.
"""


class StartupError(Exception):
    """Fatal error during server startup (lifespan)."""


class PageNotFound(Exception):
    """Requested documentation page does not exist in the source."""


class PageInvalid(Exception):
    """Page exists but failed validation (e.g., malformed frontmatter)."""


class ValidationError(Exception):
    """Input validation failure (query too short, path traversal, etc.)."""
