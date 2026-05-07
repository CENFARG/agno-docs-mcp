# agno-docs-mcp

**Servidor MCP que expone la documentación del framework Agno mediante búsqueda full-text con FTS5.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-black)](https://modelcontextprotocol.io)
[![CI](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/CENFARG/agno-docs-mcp)
[![Docs](https://img.shields.io/badge/docs-MkDocs-blue)](https://CENFARG.github.io/agno-docs-mcp/)

## ¿Qué es esto?

Un servidor [Model Context Protocol](https://modelcontextprotocol.io) que le da a los LLMs acceso rápido y preciso a la documentación del [framework Agno](https://docs.agno.com). Usa SQLite FTS5 con **ranking BM25** para búsqueda full-text en más de 3.800 páginas, con highlighting de snippets y acceso al árbol de navegación.

Construido con **arquitectura hexagonal pluggable**: `DocSource` y `SearchEngine` son puertos abstractos — cambiá implementaciones sin tocar la lógica de las herramientas.

## Demo

```
[search_docs] 'MCP agent tools':
  1. Overview                       score=-7.46  examples/tools/mcp/overview.mdx
  2. Mcp Demo                       score=-7.38  examples/agent-os/mcp-demo/overview.mdx

[get_page] 'culture/overview.mdx':
  Title: What is Culture?
  11.116 caracteres — MDX completo con ejemplos de código

[get_navigation] 7 pestañas:
  Home, SDK, AgentOS, Deploy, Examples, Reference, FAQs
```

## Instalación

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
pip install -e ".[dev]"
```

O con `uv` (sin configuración, maneja el venv automáticamente):

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
uv run mcp-agno-docs /ruta/a/agno-docs
```

> **Nota**: Próximamente en PyPI. Por ahora, instalá desde el source.

## Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| `search_docs(query, topic?, limit?)` | Búsqueda full-text con ranking BM25 y snippets resaltados en `<b>` |
| `get_page(path)` | Recuperar una página `.mdx` individual con frontmatter YAML |
| `get_navigation()` | Árbol de navegación completo desde `docs.json` |
| `search_examples(query, limit?)` | Búsqueda acotada al directorio `examples/` |

## Arquitectura

Puertos hexagonales (`DocSource`, `SearchEngine`) con inyección de dependencias. Todo el I/O bloqueante va por `asyncio.to_thread`.

## Desarrollo

```bash
pip install -e ".[dev]"
pytest                     # 204 tests
ruff check src/            # lint
mypy src/ --strict          # type check
```

## Documentación

Sitio completo: [CENFARG.github.io/agno-docs-mcp](https://CENFARG.github.io/agno-docs-mcp/)

## Licencia

Apache 2.0 — ver [LICENSE](./LICENSE).
