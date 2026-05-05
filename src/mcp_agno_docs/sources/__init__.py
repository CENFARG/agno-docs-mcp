"""Documentation source ports and adapters.

The :class:`DocSource` ABC defines the contract for loading and accessing
documentation pages. Adapters (e.g. :class:`LocalMDXSource`) implement
this contract for specific storage backends.
"""

from mcp_agno_docs.sources.base import DocSource

__all__ = ["DocSource"]
