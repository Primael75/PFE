# Diagnosis tool time on the server (complement to H-T2)

Owners: Kelyan and Fatoumata (team 2). Sprint 1 review, item 5, due 28 November.

H-T2 itself is measured on a phone, in the browser, and is passed on the
phone tested: see `ht2-latency.md`. This note measures another path: the
photo attached in Fred and diagnosed on the server by the MCP tool. It gives
no verdict on H-T2; it checks that this path also stays under the same
5-second limit.

**Done when:** the tool time is measured on the shared instance, from
Knowledge Flow, with real photos, and its p95 is reported against 5 seconds.

## Method

- The tool `diagnose_photo` (`src/agritech/diagnosis/`) is called over
  streamable HTTP, as Fred calls it, by `scripts/measure_ht2.py`.
- **20 photos** of the validation split, never the locked test split, each
  diagnosed once. Two warm-up calls are not counted. The model is loaded
  when the server starts; the load time is read in the server log.
- Read on the 95th percentile of the tool time, against 5 seconds (ENF-01 for
  the diagnosis): a mean would hide the slow calls a farmer would wait for.
- Two measures, in this order:
  1. **on the server machine, photos in a folder**: the model time on the
     instance's hardware, without the network;
  2. **from Knowledge Flow**: the photos are attached in Fred and the tool
     downloads them, as in real use.

## Procedure (Kelyan and Fatoumata)

Prerequisites: `best.pt` in `src/agritech/diagnosis/weights/` (SHA-256 in
the brick's README), `uv sync` done, 20 photos of the validation split
copied into one folder, for example `ht2-photos/`.

**Measure 1, photo folder, on the server machine.** Terminal 1:

```bash
AGRITECH_PHOTO_DIR=ht2-photos \
  uv run uvicorn agritech.diagnosis.mcp_server:create_app --factory --port 8078
```

Note the line "Model loaded in ... s" of the log. Terminal 2:

```bash
uv run python scripts/measure_ht2.py --photo-dir ht2-photos --out ht2-folder.json
```

**Measure 2, from Knowledge Flow.**

1. Attach the 20 photos in Fred, in the Agritech team, and copy their
   document uids into `ht2-uids.txt`, one per line.
2. Start the server pointing at Knowledge Flow:

   ```bash
   AGRITECH_KF_BASE_URL=http://<knowledge-flow-host>/knowledge-flow/v1 \
     uv run uvicorn agritech.diagnosis.mcp_server:create_app --factory --port 8078
   ```

3. Put a valid bearer in `AGRITECH_MEASURE_TOKEN` (never in a file under
   Git), then:

   ```bash
   uv run python scripts/measure_ht2.py --uids ht2-uids.txt --out ht2-kf.json
   ```

   If Knowledge Flow answers 401 or 403 without the delegation grant, add it
   to the query string of `--url` (`?person=...&run=...&agent=...`), as Fred
   does. The JSON file keeps the URL without its query string.

Copy the summaries of `ht2-folder.json` and `ht2-kf.json` into the table
below. The JSON files themselves stay out of Git.

## First results (21 November 2026, before the template)

Measured on a laptop with an earlier wrapper of the same model (stdio, photo
sent in the call), not yet with this tool. Intel Core i5-8365U, 16 GB, no GPU,
CPU inference. 50 CCMT photos drawn at random across the four crops (seed 42).

| Photos | Size | Calls | Median | p95 |
| --- | --- | --- | --- | --- |
| CCMT as provided | 26 to 82 KB | 50 / 50 | 0.048 s | 0.050 s |
| Enlarged to phone size (4032 x 3024) | 0.8 to 1.7 MB | 50 / 50 | 0.411 s | 0.467 s |

## Results with this tool

### Measure 1, photo folder, on Kelyan's laptop (24 November 2026)

Not yet the instance: same procedure, run on a laptop (Intel Core i5-8365U,
16 GB, no GPU, Windows, CPU inference). 20 photos sent by Fatoumata, one per
class or close (36 to 89 KB), each diagnosed once after two warm-up calls.

| Measure | Value |
| --- | --- |
| Model load time at startup | 9.8 s and 10.3 s (57 s on the very first start, right after installing PyTorch) |
| Calls | 20 / 20 answered, no error |
| Tool time seen by the client: min / median / p95 / max | 0.041 s / 0.054 s / **0.115 s** / 0.201 s |
| Model time in the server log, without HTTP | 36 to 194 ms (494 ms on the first warm-up call) |
| p95 under 5 s | **yes** |
| Answers | 19 of 20 match the class in the file name; `08_tomato_verticulium_wilt` answered `tomato_septoria_leaf_spot` (0.59). No `uncertain`: no `calibration.json` yet |

The load time is paid once, when the server starts, never on a farmer's
photo.

### Measure on the instance (to fill in)

Date: ____ . Measured by: ____ .

| Measure | Value | How |
| --- | --- | --- |
| Machine of the instance (CPU, memory, GPU) | | by hand, or `lscpu` and `free -h` |
| Model load time at startup | | server log |
| Measure 1, photo folder: calls, median / p95 / max | | `ht2-folder.json` |
| Measure 2, from Knowledge Flow: calls, median / p95 / max | | `ht2-kf.json` |
| p95 under 5 s, measure 2 | | yes / no |

## Open points

- `calibration.json` is not available yet: the model never answers
  `uncertain`. It does not change the time, only the answers.
- No off-topic class is trained yet (EF-16).
- Knowledge Flow may refuse the forwarded bearer (open question of H-T4).
  If so, measure 2 waits for the template's service identity (task M5) and
  measure 1 is reported alone, with that limit written here.
