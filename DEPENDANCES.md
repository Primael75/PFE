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
run the photo data and diagnosis tests. torch and torchvision come from the
PyTorch CPU index (`[tool.uv.index]` in `pyproject.toml`).

| Dependency | Version | Licence | Category | Reason |
| --- | --- | --- | --- | --- |
| numpy | >=2.5,<3 | BSD-3-Clause | Permissive | Photo dataset preparation: visual fingerprints and near-duplicate search |
| pillow | >=13,<14 | MIT-CMU | Permissive | Photo dataset preparation: decode each image, detect unreadable files |
| torch | >=2.15,<3, CPU build | BSD-3-Clause | Permissive | Photo diagnosis: train and run the baseline model |
| torchvision | >=0.29,<1, CPU build | BSD-3-Clause | Permissive | Photo diagnosis: MobileNetV3-Large architecture and image transforms |

## Group `rainfall`

Installed only on request (`uv sync --group rainfall`); CI installs it to
run the CHIRPS tests.

| Dependency | Version | Licence | Category | Reason |
| --- | --- | --- | --- | --- |
| rasterio | >=1.4,<2 | BSD-3-Clause | Permissive, see note | Read the CHIRPS GeoTIFFs exported from Earth Engine and rasterise the commune polygons |
| numpy | >=2.5,<3 | BSD-3-Clause | Permissive | Average the pixels of each commune, count missing and impossible values |

**Note on rasterio.** Its binary wheels bundle GDAL (MIT) and native
libraries loaded dynamically, some under weak copyleft: GEOS and libiconv
(LGPL), spatialite and freexl (MPL/GPL/LGPL tri-licence). No code of ours
links to them directly. Whether dynamically loaded LGPL libraries fit the
licence policy is left to ADR-0005, still a draft. Fallback if refused:
tifffile and imagecodecs (BSD-3-Clause), which read the same values.
## Group `dev`

Development tools, installed by `uv sync`. Only the ones added after the
initial set are listed.

| Dependency | Version | Licence | Category | Reason |
| --- | --- | --- | --- | --- |
| pyyaml | >=6,<7 | MIT | Permissive | Read the zone profiles (`config/zones/`) in their tests; becomes a runtime dependency when a brick reads them |
