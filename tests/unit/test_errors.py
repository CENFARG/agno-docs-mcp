"""Tests for domain exceptions in mcp_agno_docs.errors."""

import pytest

from mcp_agno_docs.errors import (
    PageInvalid,
    PageNotFound,
    StartupError,
    ValidationError,
)


class TestDomainExceptions:
    """Verify all domain exceptions inherit from Exception and accept messages."""

    EXCEPTION_CLASSES = [
        (StartupError, "docs_path /bogus does not exist"),
        (PageNotFound, "getting-started.mdx not found in source"),
        (PageInvalid, "malformed YAML in api/agents.mdx"),
        (ValidationError, "query must be at least 2 characters"),
    ]

    @pytest.mark.parametrize("exc_cls,message", EXCEPTION_CLASSES)
    def test_exception_inherits_from_exception(self, exc_cls: type[Exception], message: str) -> None:
        """Each domain exception MUST be a subclass of Exception."""
        assert issubclass(exc_cls, Exception), f"{exc_cls.__name__} does not inherit from Exception"

    @pytest.mark.parametrize("exc_cls,message", EXCEPTION_CLASSES)
    def test_exception_stores_and_renders_message(self, exc_cls: type[Exception], message: str) -> None:
        """Raising with a message stores it and str() returns it."""
        with pytest.raises(exc_cls, match=message):
            raise exc_cls(message)
