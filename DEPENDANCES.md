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
| httpx2 | >=2.16,<3 | BSD-3-Clause | Permissive | Photo example (H-T4): download a photo from Fred's Knowledge Flow. HTTP client already used by fastmcp and mcp; declared because the code imports it |

## Group `diagnosis`

Installed only on request (`uv sync --group diagnosis`); CI installs it to
run the photo data tests and the diagnosis model test.

| Dependency | Version | Licence | Category | Reason |
| --- | --- | --- | --- | --- |
| numpy | >=2.5,<3 | BSD-3-Clause | Permissive | Photo dataset preparation: visual fingerprints and near-duplicate search |
| pillow | >=13,<14 | MIT-CMU | Permissive | Photo dataset preparation: decode each image, detect unreadable files. Diagnosis brick: decode the photo and apply its EXIF rotation |
| torch | >=2.6,<3 | BSD-3-Clause | Permissive | Diagnosis brick: runs the trained photo model (MobileNetV3) on CPU. 2.6 or later, where `torch.load` refuses arbitrary pickled objects by default |
| torchvision | >=0.21,<1 | BSD-3-Clause | Permissive | Diagnosis brick: model architecture and image preprocessing, identical to training |
