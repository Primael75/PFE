# H-T4: an MCP tool called by an agent, which receives a photo

Owner: Messan. Sprint 1 plan, week 2.

**Done when:** the call succeeds; time and cost per request are measured
and written below.

**Status (2026-11-24):** partly failed. The agent calls the tool with the
photo's uid, but the tool cannot read a photo attached in the chat. The
path through the team's resources is still to be verified.

## What we learned from Fred's code (v3.13.0)

Read in the code running on the instance (`fred-agents` and
`knowledge-flow-backend` images v3.13.0).

- **A photo attached in the chat** is "fast-ingested" by Knowledge Flow:
  it extracts a short text (file name, format and, when a vision model is
  configured, a "Vision summary") and indexes it for the session only.
  The original file is not kept: "chat attachments no longer store a raw
  copy in workspace storage". These attachments carry no ReBAC tuple, so
  "a document-level READ check can never resolve for them"
  (`knowledge_flow_backend/features/ingestion/ingestion_controller.py`).
  As a result, `GET /knowledge-flow/v1/raw_content/{document_uid}` always
  answers 403 for them.
- **A photo imported in the team's resources** is stored as is (MinIO,
  bucket `app-content-documents`) and gets the team's permissions. This is
  the case `raw_content` is built for. It has not been verified yet with a
  call from the tool.
- The agent never receives the raw bytes. Its prompt lists the attached
  files with their document uid and says "The raw image bytes are NOT
  included in this prompt" (`fred_runtime/react/react_prompting.py`).
- Fred calls MCP servers with a bearer and a delegation grant (`person`,
  `run`, `agent`) in the query string.
- If any MCP server attached to an agent cannot be reached, Fred does not
  start the agent at all: "Agent error. The agent could not initialize its
  execution." `get_connected_mcp_client_for_agent`
  (`fred_runtime/common/mcp_utils.py`) tries every server, then raises
  `MCPConnectionError` if one failed, and throws away the tools of the
  others. There is no "optional server" setting. Fred does not explain why
  in its code; the likely reason is to avoid an agent that silently answers
  without one of its tools.

Details and file references: `src/agritech/example/README.md`, section
"Photo example (H-T4)".

## What is built

| Item | State |
| --- | --- |
| Tool `inspect_photo(document_uid)`, built with the template | Done, 9 tests |
| Reading from a local folder (tests, measures) | Done |
| Reading from Knowledge Flow, forwarding bearer and grant | Authentication accepted by the real Knowledge Flow; reading refused for chat attachments (403); team documents to verify |
| Script measuring the tool time over HTTP | Done: `scripts/measure_ht4.py` |
| Declared in Fred's catalog and called by an agent | Done on the local k3d instance |

## Trial on the local instance, 2026-11-24

Setup: local k3d cluster `fred`, Fred v3.13.0, model
`mistral-medium-latest`, vision model `pixtral-12b-2409`. The server runs
in WSL:

```bash
AGRITECH_KF_BASE_URL=http://localhost:8088/knowledge-flow/v1 \
  uv run uvicorn agritech.example.photo_mcp_server:create_app --factory \
  --host 0.0.0.0 --port 8077
```

It is declared in the catalog (`deploy/k3d/fred-values.yaml`) at
`http://host.docker.internal:8077/mcp`. In the pods, `host.docker.internal`
resolves; `host.k3d.internal` does not.

### What happened

1. **Server not started.** Every turn of the agent fails with "Agent
   error", even though the agent has other tools: see the last point of
   the section above.
2. **Photo attached in the chat** (two photos, same result):
   - the agent calls `inspect_photo` with the document uid, not the file
     name;
   - the server asks Knowledge Flow for the photo; Knowledge Flow accepts
     the grant (`delegation.grant.accepted`), then refuses the read
     (`ReBAC authorization denied: permission=read resource_type=document`,
     403);
   - the tool fails ("This step failed unexpectedly"), and the agent
     answers that it cannot see the image.
3. **Photo imported in the team's resources.** The agent describes the
   image, but it does not call `inspect_photo`: it calls Fred's
   `search_documents_using_vectorization` and answers from the vision
   summary. Our server received no call, so the download from
   `raw_content` was not exercised.

### Answers to the open questions

- *Does Knowledge Flow accept the forwarded bearer and grant?* For
  authentication, yes. Whether the read is allowed depends on the
  document: it is always refused for a chat attachment.
- *Does the agent pass the uid, not the file name?* Yes.

### Problems found

1. **The tool cannot read a photo attached in the chat.** This blocks
   the diagnosis axis: Knowledge Flow neither keeps the file nor grants a
   right to read it.
2. **The language model only sees a text description.** In both cases,
   what reaches the model is the description written by Fred's vision
   model at import. A general description is not a diagnosis: our
   diagnosis model needs the photo itself.
3. **The agent prefers document search to our tool** when the photo is a
   team document. Its prompt or settings must direct it to the tool.
4. **A figure without a source.** In run 2, the tool failed, yet the agent
   wrote "Format: JPEG (122 990 octets)". The size is neither in the
   attachment list of Fred's prompt nor in the text extracted at import.
   To check against the real file size; if the model made it up, it breaks
   the rule "the language model never produces a number".
5. **One unreachable MCP server blocks the whole agent.** A server under
   development must be attached to a test agent only.

## Next steps (to decide)

1. Verify the team-document path end to end: import a photo in the team's
   resources, ask the agent to call `inspect_photo` on its uid, expect a
   200 from `raw_content`, then fill in the results below.
2. Decide how the photo reaches the diagnosis model:

   | Option | Idea | Limit |
   | --- | --- | --- |
   | A | The farmer imports the photo in the team's resources, not in the chat | Less natural to use; the agent must be steered to the tool |
   | B | An Agritech application in Fred receives the photo and calls our service | More work; a structural choice that needs an ADR |
   | C | Ask the Fred team for a delegated read of chat attachments | Goes against their choice not to keep the original file |

## Results

| Measure | Value | How |
| --- | --- | --- |
| Tool time alone, local folder, median / p95 | 3 ms / 12 ms (20 calls, test machine) | `scripts/measure_ht4.py` |
| Tool time alone, from Knowledge Flow, median / p95 | Not measured: no successful read yet | `scripts/measure_ht4.py` on the instance |
| Failed tool call (403), as seen by the agent | 256 ms | `latency_ms` in Fred's trace, run 2 |
| Whole agent turn, median / p95 | | timings shown in Fred, 10 turns |
| Tokens per turn (input + output) | 16,044 (15,828 + 216), one turn of run 2 | total shown in Fred |
| Cost per turn | | tokens x price of the model used |
| Verdict | Partly failed: the call reaches the tool with the uid, but a chat attachment cannot be read. Team-document path to verify | |


## Verdict (2026-11-24)

**Partly failed.** A Fred agent calls the MCP tool with the document uid,
and Knowledge Flow accepts the forwarded identity. But a photo attached in
the chat cannot be read by the tool (403): Fred does not keep the original
file.

**Fallback:** option A for sprint 2 (photo imported into the team's
resources), subject to a trial of `raw_content`; option B as the target
(an Agritech application receives the photo), to be decided in ADR-0003.
Option C asked to the Fred team, for information only.

**Finding to fix:** the agent gave a file size although the tool had
failed. A guardrail is to be added in sprint 2 (`agents/` brick), with a
test.
