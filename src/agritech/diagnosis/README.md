# diagnosis

## Purpose
Photo diagnosis of crop diseases: suspected disease, confidence level,
abstention when unsure, rejection of off-topic photos. A light version
runs on the phone.

## Owner
Team 2 (Diagnosis).

## Provides
The diagnosis tool and the offline mode of the application, to all teams.

## Status
Sprint 1: the diagnosis tool `diagnose_photo` is built from the MCP server
template (case A) and measured for H-T2. Calibration (`calibration.json`)
and the off-topic class come in sprint 2.

## Files

| File | Layer | Role |
| --- | --- | --- |
| `diagnosis.py` | Domain | Turns class probabilities into a `SourcedValue`: class, `uncertain` or `off_topic`. No MCP, no PyTorch |
| `classifier.py` | Adapter | The trained network (MobileNetV3) behind the `Classifier` protocol, with the training preprocessing |
| `mcp_server.py` | Adapter, case A | The tool `diagnose_photo(document_uid)`, served over streamable HTTP |
| `weights/` | Data | `best.pt` (trained weights) and, once computed, `calibration.json` |
| `tests/diagnosis/test_diagnosis.py` | Tests | Every layer without an agent; a fake classifier, except one test on the real network with random weights |
| `scripts/measure_ht2.py` | Measure | Tool time over HTTP, for H-T2 |

## The tool: `diagnose_photo(document_uid)`

The photo is read as in the template's photo example (H-T4): the agent passes
the document uid of the photo attached in Fred, and the tool downloads its
bytes from Knowledge Flow. The result is a `SourcedValue`:

| Field | Content |
| --- | --- |
| `value` | The class name (for example `cassava_mosaic`), `uncertain` when the confidence is below the calibrated threshold, or `off_topic` |
| `unit` | `label` |
| `source` | The model: file name and number of classes |
| `as_of` | The day of the diagnosis: the photo's upload date is not known to the tool |
| `uncertainty` | Confidence of the most likely class, between 0 and 1 |

An unreadable or missing photo returns `missing_data(...)`, an explicit error.
Class names keep the spelling of the training dataset (for example
`maize_grasshoper`): they are the keys of the fact sheets, not display names.

## Run locally

From the repository root, with the weights in `src/agritech/diagnosis/weights/`.
The model needs the `diagnosis` dependency group (PyTorch):

```bash
uv sync --group diagnosis

# Reading photos from a local folder: the file name is the uid
AGRITECH_PHOTO_DIR=/path/to/photos \
  uv run uvicorn agritech.diagnosis.mcp_server:create_app --factory --port 8078

# H-T2: tool time alone, over HTTP, on the same folder
uv run python scripts/measure_ht2.py /path/to/photos --url http://127.0.0.1:8078/mcp --runs 50

# In Fred: read photos from Knowledge Flow
AGRITECH_KF_BASE_URL=http://<knowledge-flow-host>/knowledge-flow/v1 \
  uv run uvicorn agritech.diagnosis.mcp_server:create_app --factory --port 8078
```

`AGRITECH_DIAGNOSIS_MODEL` points to other weights. The model is loaded once,
when the server starts.

## Deviations from the template

| What | Why | Impact |
| --- | --- | --- |
| `value` carries `uncertain` or `off_topic` instead of a class name | `SourcedValue` has a single value; abstaining is a valid answer, not missing data. Agreed with the Diagnosis team | The agent must treat these two values as answers, not as diseases |
| The other likely classes are dropped | Same reason; to revisit when an agent needs them | The agent sees only the most likely class |
| Imports `PhotoSource` from `agritech.example.photo_source` | Reuse, not duplicate: the same Knowledge Flow reading as H-T4 | Same deviation as H-T4 (forwarded bearer and grant). The module could move to `core` |
| PyTorch is in the `diagnosis` dependency group, not a runtime dependency | The model needs it; it is imported only when the real model runs, so the other bricks and the domain tests run without it | The server needs `uv sync --group diagnosis`. CI already installs this group, so it downloads PyTorch from PyPI (large, CUDA build). A CPU-only index could reduce it, to decide with the project lead |

## Checkpoint contract

`best.pt` is a dictionary with `classes` (list of class names), `img_size`
(side of the square input) and `state_dict` (MobileNetV3-Large weights, last
layer resized to the number of classes). It is loaded with
`torch.load(weights_only=True)`, which refuses any other pickled object: a
checkpoint saved with extra Python objects must be saved again with these
three keys only.

`calibration.json` holds `temperature` (divides the scores before softmax)
and `threshold` (abstention threshold), both computed on the validation set.
Without it the model never abstains, and the server logs a warning.
