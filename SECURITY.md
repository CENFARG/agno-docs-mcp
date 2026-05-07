# Security Policy

## Supported Versions

Security updates are provided for the following versions:

| Version | Supported          | Python       |
| ------- | ------------------ | ------------ |
| 0.1.x   | :white_check_mark: | 3.11, 3.12   |
| < 0.1.0 | :x:                | —            |

## Reporting a Vulnerability

**Do not open a public issue.** Instead, report vulnerabilities privately so we can patch them before they are disclosed.

### Preferred: GitHub Security Advisories

1. Go to **Security → Advisories** on the [repository](https://github.com/CENFARG/agno-docs-mcp/security/advisories)
2. Click **New draft security advisory**
3. Fill in the form describing the vulnerability
4. Submit — the maintainers will be notified immediately

### Alternative: Email

If you cannot use GitHub Security Advisories, send an encrypted report to:

- **Email**: gonzalo@agno.ai
- **PGP Key**: [Available on request](https://github.com/gonzalorrecalde.gpg)

Please include in your report:

- A clear description of the vulnerability
- Steps to reproduce (proof-of-concept code if possible)
- Affected versions
- Potential impact
- Suggested fix (if you have one)

### What to Expect

| Phase | Timeline | Description |
| ----- | -------- | ----------- |
| Acknowledgment | Within **48 hours** | We confirm receipt and assign a severity |
| Triage | Within **5 business days** | We reproduce and assess the report |
| Fix development | Varies by severity | Critical: ~72h, High: ~7d, Medium: next release |
| Disclosure | Coordinated with reporter | CVE requested if applicable |

### Severity Classification

| Severity | Example |
| -------- | ------- |
| **Critical** | Remote code execution via MCP tool input |
| **High** | Path traversal exposing files outside doc root |
| **Medium** | Denial of service via crafted search queries |
| **Low** | Information disclosure in error messages |

## Disclosure Policy

1. The reporter and maintainers agree on a disclosure date
2. A CVE identifier is requested (for Critical/High)
3. A fix is prepared and merged privately
4. A security release is published with a full advisory
5. Credit is given to the reporter (with permission)

## Scope

Security reports are accepted for:

- The `agno-docs-mcp` server and its MCP tools
- The built-in `FTS5Engine` and `LocalMDXSource` adapters
- Input validation, path handling, and query sanitization
- Dependencies with known vulnerabilities

## Out of Scope

- Vulnerabilities in the upstream [Agno documentation](https://github.com/agno-agi/agno-docs) content
- Issues requiring physical access to the host machine
- Social engineering attacks
- Third-party MCP client vulnerabilities

## Security Best Practices

- **Input validation**: All tool inputs are validated via Pydantic v2 schemas
- **Path safety**: File paths are resolved and sandboxed within the documentation root
- **Least privilege**: The server only reads — it never writes to disk
- **Dependencies**: Pinned in `pyproject.toml`; audited with `pip-audit`
- **CI enforcement**: Ruff linting and Mypy strict mode block unsafe patterns

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [MCP Security Considerations](https://modelcontextprotocol.io/docs/concepts/security)
- [Coordinated Vulnerability Disclosure](https://certcc.github.io/CERT-Guide-to-CVD/)
