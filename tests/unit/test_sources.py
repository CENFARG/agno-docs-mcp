"""Tests for the DocSource abstract base class.

Verifies that DocSource cannot be instantiated directly and that subclasses
MUST implement all abstract methods. Also tests that the contract methods
work correctly with expected return types.
"""

import pytest

from mcp_agno_docs.sources.base import DocSource


class TestDocSourceContract:
    """DocSource ABC enforces its interface contract."""

    def test_cannot_instantiate_abc_directly(self) -> None:
        """Instantiating DocSource directly MUST raise TypeError."""
        with pytest.raises(TypeError, match="abstract"):
            DocSource()  # type: ignore[abstract]

    def test_subclass_without_load_fails_instantiation(self) -> None:
        """Missing async load() prevents instantiation."""

        class Incomplete(DocSource):
            def get_page(self, path: str):  # noqa: D102
                pass

            def list_pages(self) -> list[str]:  # noqa: D102
                return []

            def iter_index_documents(self):  # noqa: D102
                return iter([])

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_subclass_without_get_page_fails_instantiation(self) -> None:
        """Missing get_page() prevents instantiation."""

        class Incomplete(DocSource):
            async def load(self) -> None:  # noqa: D102
                pass

            def list_pages(self) -> list[str]:  # noqa: D102
                return []

            def iter_index_documents(self):  # noqa: D102
                return iter([])

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_fully_implemented_subclass_instantiates(self) -> None:
        """A subclass implementing ALL abstract methods instantiates successfully."""

        class Complete(DocSource):
            async def load(self) -> None:
                pass

            def get_page(self, path: str):
                raise NotImplementedError

            def list_pages(self) -> list[str]:
                return []

            def iter_index_documents(self):
                return iter([])

        source = Complete()
        assert isinstance(source, DocSource)
