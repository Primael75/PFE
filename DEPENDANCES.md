# Dependencies

Every runtime dependency, with its licence. See the licence policy in
`AGENTS.md`.

| Dependency | Version | Licence | Category | Reason |
| --- | --- | --- | --- | --- |
| pydantic | >=2,<3 | MIT | Permissive | Common output format of MCP tools (`SourcedValue`), with validation |
| fastmcp | >=4.1.3,<5 | Apache-2.0 | Permissive | MCP server framework, same constraint as Fred's Knowledge Flow |
| mcp | >=2.3.0,<3 | MIT | Permissive | MCP protocol SDK, same constraint as Fred's Knowledge Flow |
| fastapi | unconstrained (to align with Knowledge Flow) | MIT | Permissive | Case B of the template: an API route also exposed as an MCP tool |
| uvicorn | unconstrained (to align with Knowledge Flow) | BSD-3-Clause | Permissive | ASGI server that runs MCP servers over streamable HTTP |
