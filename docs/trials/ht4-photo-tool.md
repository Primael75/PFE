# H-T4: an MCP tool called by an agent, which receives a photo

Owner: Messan. Sprint 1 plan, week 2.

**Done when:** the call succeeds; time and cost per request are measured
and written below.

## What we learned from Fred's code (v3.13.0, commit c4403b5)

- An attached photo goes to Knowledge Flow. The agent only gets its
  **document uid**; the raw bytes are never in the prompt.
- A tool therefore takes a `document_uid` and downloads the photo with
  `GET /knowledge-flow/v1/raw_content/{document_uid}`. Knowledge Flow
  accepts either a signed-in person or a person named by a trusted
  workload (delegation grant: `person`, `run`, `agent`).
- Fred calls MCP servers with a bearer and that grant in the query string.

Details and file references: `src/agritech/example/README.md`, section
"Photo example (H-T4)".

## What is built

| Item | State |
| --- | --- |
| Tool `inspect_photo(document_uid)`, built with the template | Done, 9 tests |
| Reading from a local folder (tests, measures) | Done |
| Reading from Knowledge Flow, forwarding bearer and grant | Done, tested with a mock; to confirm against the real Knowledge Flow |
| Script measuring the tool time over HTTP | Done: `scripts/measure_ht4.py` |
| Declared in Fred's catalog and called by an agent | To do on the shared instance |

## Trial on the shared instance

1. Start the server in WSL, pointing at Knowledge Flow (address to confirm:
   the one Fred's front end uses, behind port 8088).
2. Declare it in Fred's catalog with `transport: streamable_http` and an
   address the cluster can reach (with k3d, the host is usually
   `host.k3d.internal`; to confirm).
3. Enable it for the Agritech team (Admin, Features), attach it to an agent.
4. In a conversation, attach a photo and ask for its format and size.
5. Repeat 10 times with different photos and fill in the table.

Open questions for the trial:

- Does Knowledge Flow accept the forwarded bearer and grant? If it answers
  401 or 403, Fred stops the run with "no longer authorized to act for
  you" (`fred_runtime/common/kf_base_client.py`).
- Does the agent pass the uid, not the file name? Its prompt tells it to.

## Results (to fill in)

| Measure | Value | How |
| --- | --- | --- |
| Tool time alone, local folder, median / p95 | 3 ms / 12 ms (20 calls, test machine) | `scripts/measure_ht4.py` |
| Tool time alone, from Knowledge Flow, median / p95 | | `scripts/measure_ht4.py` on the instance |
| Whole agent turn, median / p95 | | timings shown in Fred, 10 turns |
| Tokens per turn (input + output) | | total shown in Fred |
| Cost per turn | | tokens x price of the model used |
| Verdict | | succeeded / failed, and the fallback if failed |
