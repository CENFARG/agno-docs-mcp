# Authors

## Maintainer

**Gonzalo Recalde** — <gonzalo@agno.ai>

Gonzalo is the creator and primary maintainer of agno-docs-mcp. He designed the hexagonal architecture, wrote the initial FTS5 engine adapter, and established the project's quality standards.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%">
        <a href="https://github.com/gonzalorrecalde">
          <img src="https://github.com/gonzalorrecalde.png?s=100" width="100px;" alt="Gonzalo Recalde"/>
          <br />
          <sub><b>Gonzalo Recalde</b></sub>
        </a>
        <br />
        <a href="https://github.com/CENFARG/agno-docs-mcp/commits?author=gonzalorrecalde" title="Code">💻</a>
        <a href="#design-gonzalorrecalde" title="Design">🎨</a>
        <a href="https://github.com/CENFARG/agno-docs-mcp/commits?author=gonzalorrecalde" title="Documentation">📖</a>
        <a href="#infra-gonzalorrecalde" title="Infrastructure">🚇</a>
        <a href="https://github.com/CENFARG/agno-docs-mcp/commits?author=gonzalorrecalde" title="Tests">⚠️</a>
      </td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://allcontributors.org) specification. Contributions of any kind are welcome — code, docs, design, testing, and more.

## Acknowledgments

agno-docs-mcp is built on the shoulders of remarkable open-source projects:

- **[FastMCP](https://github.com/jlowin/fastmcp)** by Jeremiah Lowin — elegant MCP server framework that abstracts the protocol complexity
- **[SQLite FTS5](https://www.sqlite.org/fts5.html)** — the search engine that ships with Python and handles 3,800 documents without breaking a sweat
- **[Pydantic v2](https://docs.pydantic.dev)** — type-safe data validation that catches errors at the protocol boundary before they reach tool logic
- **[Agno](https://github.com/agno-agi/agno)** — the framework whose excellent documentation inspired this project
- **[MCP](https://modelcontextprotocol.io)** — the protocol that makes tools like this possible, designed by Anthropic
- **[Porter Stemmer](https://tartarus.org/martin/PorterStemmer/)** — Martin Porter's algorithm from 1980, still the best stemmer for English technical text
