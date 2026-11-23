# H-T2: the diagnosis model, exposed as an MCP tool, answers in less than 5 seconds on the server

Owners: Kelyan and Fatoumata (team 2). Sprint 1 plan.

**Done when:** the tool time is measured on the shared instance, from
Knowledge Flow, with real photos, and its p95 is below 5 seconds.

## Method

- The tool `diagnose_photo` (`src/agritech/diagnosis/`) is called over
  streamable HTTP, as Fred calls it, by `scripts/measure_ht2.py`.
- The model is loaded when the server starts. Two warm-up calls are not
  counted; the load time is read in the server log.
- Verdict on the 95th percentile of the tool time: a mean would hide the slow
  calls that a farmer would actually wait for.
- Photos: 30 to 50 photos of the validation set, never the locked test set.

## First results (21 November 2026, before the template)

Measured on a laptop with an earlier wrapper of the same model (stdio, photo
sent in the call), not yet with this tool. Intel Core i5-8365U, 16 GB, no GPU,
CPU inference. 50 CCMT photos drawn at random across the four crops (seed 42).

| Photos | Size | Calls | Median | p95 |
| --- | --- | --- | --- | --- |
| CCMT as provided | 26 to 82 KB | 50 / 50 | 0.048 s | 0.050 s |
| Enlarged to phone size (4032 x 3024) | 0.8 to 1.7 MB | 50 / 50 | 0.411 s | 0.467 s |

## Results with this tool (to fill in)

| Measure | Value | How |
| --- | --- | --- |
| Model load time at startup | | server log |
| Tool time, local folder, median / p95 | | `scripts/measure_ht2.py` |
| Tool time, from Knowledge Flow on the instance, median / p95 | | `scripts/measure_ht2.py`, server with `AGRITECH_KF_BASE_URL` |
| Machine of the instance (CPU, memory, GPU) | | |
| Verdict | | passed / failed |

## Open points

- `calibration.json` is not available yet: the model never answers
  `uncertain`. It does not change the time, only the answers.
- No off-topic class is trained yet (EF-16).
