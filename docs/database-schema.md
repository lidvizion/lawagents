# Database Schema (MongoDB)

When `MONGODB_URI` is set, tools and integrations are stored for agent lookup.

## Collections

### tools

| Field | Type | Description |
|-------|------|-------------|
| slug | string | Unique identifier |
| name | string | Display name |
| category | string | practice-management, legal-ai, court-data, legislative-api, etc. |
| use_when | string | When to use this tool |
| path | string | Path to catalog markdown |
| score | number | Composite score 0–10 |
| has_api | boolean | Has REST/API access |
| has_mcp | boolean | Has MCP (Model Context Protocol) support |
| provider | string | Vendor/provider |
| url | string | Product or API URL |
| source | string | datarade, catalog, etc. |
| last_synced | string | ISO timestamp |

**Indexes:** slug (unique), category, has_mcp, last_synced

### integrations

| Field | Type | Description |
|-------|------|-------------|
| slug | string | Unique identifier |
| name | string | Display name |
| type | string | mcp, api, zapier |
| tool_slug | string | Related tool slug |
| url | string | Integration URL |

**Indexes:** slug (unique), tool_slug, type

## has_mcp Flag

Tools with MCP support (e.g., Zapier Clio MCP, Buffer, Hootsuite) have `has_mcp: true`. TrustFoundry AI, LegiScan, OpenLaws, Bloomberg Dockets API have `has_mcp: false`. Update when vendors add MCP support.
