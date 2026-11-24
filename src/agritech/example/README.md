# example: the MCP server template

This brick is the reference for every MCP server of the project. Copy it
and adapt it; any deviation from an accepted ADR is declared as described
in `AGENTS.md`. The data is fictitious.

## Files

| File | Layer | Role |
| --- | --- | --- |
| `prices.py` | Domain | The calculation, in plain Python. No MCP, no HTTP |
| `mcp_server.py` | Adapter, case A | The calculation exposed as a native MCP tool |
| `api.py` | Adapter, case B | The calculation exposed as an API route, also an MCP tool |
| `tests/example/test_example.py` | Tests | Every layer tested without an agent |
| `photo.py`, `photo_source.py`, `photo_mcp_server.py` | Photo example (H-T4) | A tool that receives a photo sent in Fred, see below |
| `tests/example/test_photo.py` | Tests | The photo example, without an agent |

## Which case to choose

- **Case A**: the calculation is used by agents only.
- **Case B**: the calculation is also used by our own interface, through
  the REST API. Only routes tagged `mcp` become tools.

## Add a tool in your brick

1. **Domain**: in `src/agritech/<brick>/`, write a function that returns a
   `SourcedValue`, or `None` when the data is missing. It must not import
   anything from MCP or FastAPI.
2. **Adapter**: copy `mcp_server.py` (case A) or `api.py` (case B) into
   your brick. Give the tool typed parameters and a clear docstring: the
   model reads it to decide when to call the tool.
3. **Missing data**: return `missing_data(...)` (case A) or raise
   `HTTPException(404)` (case B). Never return an invented value (ENF-03).
4. **Tests**: create `tests/<brick>/test_<module>.py`, from
   `tests/example/test_example.py`. Test file names must be unique across
   the project.
5. **Check**: run `make check`, then open a pull request.

## The output format: `SourcedValue`

Defined in `agritech/core/tool_output.py`.

| Field | Content |
| --- | --- |
| `value` | A number, or a text such as a disease name |
| `unit` | `XOF/kg`, `mm`... Use `label` for a text value and `day of year` for a date in a range |
| `source` | `name`, and `url` for anything found online (EF-05) |
| `as_of` | The date of the data, not of the computation |
| `uncertainty` | An `Interval` (`low`, `high`), a probability between 0 and 1, or `None` |

`to_tool_result()` turns it into the MCP result: a text that cites the
source, read by the model, and the structured data.

## Logging

- One logger per module: `logger = logging.getLogger(__name__)`.
- Never `print`: in stdio, stdout carries the MCP protocol. Ruff rejects
  it (rule `T20`).
- Logging is configured once, by the entry point, with
  `configure_logging()` from `agritech/core/logging_config.py`.

## Run locally

From the repository root:

```bash
# Case A over streamable HTTP, as Fred will call it
uv run uvicorn agritech.example.mcp_server:create_app --factory --port 8000

# Case A or B over stdio, for a local MCP client
uv run python -m agritech.example.mcp_server
uv run python -m agritech.example.api
```

## Declaring a server in Fred

The catalog entry must set `transport: streamable_http` explicitly: the
default is `sse`, which Fred 3.13 refuses. Authentication and delegation
come in the next version of the template.

## Photo example (H-T4): a tool that receives a photo

### How a photo reaches a tool in Fred 3.13

Read in Fred's code at the pinned commit:

1. A photo attached in the chat is uploaded to Knowledge Flow and indexed
   (an extracted vision description is searchable).
2. The agent never receives the raw bytes. Its prompt lists the attached
   files with their **document uid** and says: "The raw image bytes are NOT
   included in this prompt" (`fred_runtime/react/react_prompting.py`).
3. So a tool takes a `document_uid` parameter, and downloads the original
   bytes from Knowledge Flow: `GET /knowledge-flow/v1/raw_content/{document_uid}`
   (`knowledge_flow_backend/features/content/content_controller.py`).
   Knowledge Flow checks that the person may read the document.

   **Limit found in the trial:** this works only for a document imported in
   the team's resources. A photo attached in the chat keeps no original
   file and no read permission, so `raw_content` answers 403
   (`knowledge_flow_backend/features/ingestion/ingestion_controller.py`).
   See `docs/trials/ht4-photo-tool.md`.
4. Fred calls an MCP server with a bearer and a delegation grant
   (`person`, `run`, `agent`) in the query string
   (`fred_core/security/mcp_delegation.py`).

Never pass the photo itself as a tool argument: the model would have to
write it out in base64, which costs tokens and fails on large photos.

### Run it

```bash
# Reading photos from a local folder: the file name is the uid
AGRITECH_PHOTO_DIR=/path/to/photos \
  uv run uvicorn agritech.example.photo_mcp_server:create_app --factory --port 8000

# Tool time alone, over HTTP
uv run python scripts/measure_ht4.py <file-name> --runs 20

# In Fred: read photos from Knowledge Flow
AGRITECH_KF_BASE_URL=http://<knowledge-flow-host>/knowledge-flow/v1 \
  uv run uvicorn agritech.example.photo_mcp_server:create_app --factory --port 8000
```

### Deviation (H-T4 only)

`KnowledgeFlowPhotoSource` forwards to Knowledge Flow the bearer and the
grant that Fred sent to the tool. This is acceptable for a demo on our own
instance, but the MCP security guidance advises against passing a received
token on to another service. The next version of the template will give
the server its own service identity, which sends its own token with the
grant, as Fred's own servers do. To decide with ADR-0002 or a new ADR.
