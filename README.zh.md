# agno-docs-mcp

**基于 FTS5 全文搜索的 Agno 框架文档 MCP 服务器。**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-black)](https://modelcontextprotocol.io)
[![CI](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/CENFARG/agno-docs-mcp)
[![Docs](https://img.shields.io/badge/docs-MkDocs-blue)](https://CENFARG.github.io/agno-docs-mcp/)

## 这是什么？

一个 [Model Context Protocol](https://modelcontextprotocol.io) 服务器，为 LLM 提供对 [Agno 框架](https://docs.agno.com) 文档的快速准确访问。使用 SQLite FTS5 配合 **BM25 排序**，在 3,800 多页文档中进行全文搜索，支持片段高亮和导航树访问。

采用 **可插拔六边形架构**构建：`DocSource` 和 `SearchEngine` 是抽象端口——无需更改工具逻辑即可替换实现。

## 演示

```
[search_docs] 'MCP agent tools':
  1. Overview                       score=-7.46  examples/tools/mcp/overview.mdx
  2. Mcp Demo                       score=-7.38  examples/agent-os/mcp-demo/overview.mdx

[get_page] 'culture/overview.mdx':
  标题: What is Culture?
  11,116 字符 — 包含代码示例的完整 MDX

[get_navigation] 7 个标签页:
  Home, SDK, AgentOS, Deploy, Examples, Reference, FAQs
```

## 安装

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
pip install -e ".[dev]"
```

或使用 `uv`：

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
uv run mcp-agno-docs /path/to/agno-docs
```

> **注意**：即将发布到 PyPI。目前请从源码安装。

## 工具

| 工具 | 描述 |
|------|------|
| `search_docs(query, topic?, limit?)` | 使用 BM25 排序和 `<b>` 高亮的全文搜索 |
| `get_page(path)` | 检索单个 `.mdx` 页面及 YAML frontmatter |
| `get_navigation()` | 从 `docs.json` 获取完整导航树 |
| `search_examples(query, limit?)` | 限定在 `examples/` 目录中搜索 |

## 架构

六边形端口（`DocSource`、`SearchEngine`）配合依赖注入。所有阻塞 I/O 通过 `asyncio.to_thread` 处理。

## 开发

```bash
pip install -e ".[dev]"
pytest                     # 204 个测试
ruff check src/            # 代码检查
mypy src/ --strict          # 类型检查
```

## 文档

完整文档站点：[CENFARG.github.io/agno-docs-mcp](https://CENFARG.github.io/agno-docs-mcp/)

## 许可证

Apache 2.0 — 详见 [LICENSE](./LICENSE)。
