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
Baseline model trained on CCMT (Ghana), scored per class on the validation
split, H-T2 passed on the phone tested with the 32-bit ONNX export (see
`docs/trials/ht2-latency.md`). Exposed to Fred as the MCP tool
`diagnose_photo` (see below). Calibration (`calibration.json`) and the
off-topic class come in sprint 2.

| Module | Role |
| --- | --- |
| `model.py` | MobileNetV3-Large, preprocessing contract, dataset, checkpoint loading |
| `train.py` | Two-stage training; reads `train.csv` and `val.csv` only |
| `evaluate.py` | Precision, recall and F1 per class on the validation split |
| `latency.py` | Response time per photo with PyTorch (reference for H-T2) |
| `diagnosis.py` | Domain: turns class probabilities into a `SourcedValue` (class, `uncertain` or `off_topic`). No MCP, no PyTorch |
| `classifier.py` | Adapter: the trained network behind the `Classifier` protocol, loaded and preprocessed through `model.py` |
| `mcp_server.py` | Adapter, template case A: the tool `diagnose_photo(document_uid)`, served over streamable HTTP |
| `weights/` | Where the server looks for `best.pt` and, once computed, `calibration.json` (outside Git: see `weights/README.md`) |

The splits come from `agritech.data.prepare_data` (see `docs/data/ccmt.md`).
Weights, runs and photos stay outside Git.

## Usage

From the repository root:

```bash
uv sync --group diagnosis
uv run python -m agritech.diagnosis.train --data data_ccmt --out runs/run1 --epochs-ft 0
uv run python -m agritech.diagnosis.evaluate --data data_ccmt --model runs/run1/best.pt --out runs/run1/val_scores.json
uv run python -m agritech.diagnosis.latency --data data_ccmt --model runs/run1/best.pt --out runs/run1/latency.json
```

`train` downloads the ImageNet weights of torchvision on first use (see the
open point in `docs/trials/ht3-licences.md`).

## Preprocessing contract

Any client of the model (server, phone) must reproduce it exactly; it is
also written to `config.json` next to the weights.

- open the photo, apply the EXIF rotation, convert to RGB;
- resize directly to 224 x 224, no crop;
- scale values to [0, 1], normalise with the ImageNet mean
  (0.485, 0.456, 0.406) and standard deviation (0.229, 0.224, 0.225);
- tensor NCHW, float32.

## Baseline model (run1)

| Field | Value |
| --- | --- |
| Architecture | MobileNetV3-Large, ImageNet weights, new last layer for 22 classes |
| Training | Stage 1 only: last layer trained, 5 epochs, learning rate 1e-3, batch 32, class weights, label smoothing 0.05, seed 42. Stage 2 (fine-tuning of the last blocks) not run yet |
| Data | CCMT split of `docs/data/ccmt.md`: 16,983 training photos, 3,656 validation photos; test split not used |
| Weights | `best.pt`, 17.1 MB, outside Git, SHA-256 `da24a99f6d601c9783289f0ebb83ed6ae2515a284e7f223a49247b67d178b551` |
| Validation accuracy | 0.834 (3,049 of 3,656 photos) |
| Macro F1 | 0.827 |

### Scores per class, validation split

Recall: share of the photos of the class that are recognised. Precision:
share of the answers "this class" that are right.

| Class | Photos | Precision | Recall | F1 | Most confused with |
| --- | ---: | ---: | ---: | ---: | --- |
| cashew_anthracnose | 260 | 0.946 | 0.742 | 0.832 | cashew_healthy (24) |
| cashew_gumosis | 59 | 0.908 | 1.000 | 0.952 | none |
| cashew_healthy | 205 | 0.854 | 0.971 | 0.909 | cashew_leaf_miner (2) |
| cashew_leaf_miner | 207 | 0.849 | 0.976 | 0.908 | cashew_anthracnose (4) |
| cashew_red_rust | 253 | 0.979 | 0.933 | 0.956 | cashew_healthy (6) |
| cassava_bacterial_blight | 390 | 0.924 | 0.839 | 0.879 | cassava_brown_spot (32) |
| cassava_brown_spot | 220 | 0.848 | 0.909 | 0.877 | cassava_bacterial_blight (15) |
| cassava_green_mite | 153 | 0.860 | 0.882 | 0.871 | cassava_mosaic (8) |
| cassava_healthy | 179 | 0.891 | 0.955 | 0.922 | cassava_green_mite (5) |
| cassava_mosaic | 167 | 0.895 | 0.916 | 0.905 | cassava_green_mite (6) |
| maize_fall_armyworm | 43 | 0.892 | 0.767 | 0.825 | maize_leaf_spot (8) |
| maize_grasshoper | 101 | 0.950 | 0.941 | 0.945 | maize_fall_armyworm (3) |
| maize_healthy | 31 | 0.625 | 0.968 | 0.759 | cashew_healthy (1) |
| maize_leaf_beetle | 140 | 0.985 | 0.950 | 0.967 | maize_leaf_spot (3) |
| maize_leaf_blight | 149 | 0.820 | 0.765 | 0.792 | maize_leaf_spot (23) |
| maize_leaf_spot | 157 | 0.734 | 0.720 | 0.727 | maize_healthy (16) |
| maize_streak_virus | 138 | 0.821 | 0.927 | 0.871 | maize_leaf_spot (7) |
| tomato_healthy | 71 | 0.867 | 0.915 | 0.890 | tomato_leaf_blight (2) |
| tomato_leaf_blight | 195 | 0.610 | 0.441 | 0.512 | tomato_septoria_leaf_spot (61) |
| tomato_leaf_curl | 78 | 0.608 | 0.577 | 0.592 | tomato_septoria_leaf_spot (16) |
| tomato_septoria_leaf_spot | 346 | 0.716 | 0.737 | 0.727 | tomato_verticulium_wilt (32) |
| tomato_verticulium_wilt | 114 | 0.513 | 0.675 | 0.583 | tomato_septoria_leaf_spot (19) |

### Reading

- **Tomato is the weak crop**: the four tomato diseases have an F1 between
  0.51 and 0.73. `tomato_leaf_blight` is recognised in fewer than half of
  the cases, mostly mistaken for `tomato_septoria_leaf_spot` (61 of 195).
- **Maize leaf diseases** (`leaf_blight`, `leaf_spot`) are confused with
  each other and with healthy leaves.
- **Small classes** (`maize_healthy`: 31 photos, `maize_fall_armyworm`: 43)
  have imprecise scores.
- **Errors stay within the crop**: the most frequent confusion of each
  class is another class of the same crop, except for `maize_healthy`
  (1 photo taken for `cashew_healthy`).
- These are validation scores on CCMT photos (Ghana, 400 x 400 squares);
  the score on phone photos from Benin is still to be measured.

## MCP tool: `diagnose_photo(document_uid)`

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

## Serve the tool

From the repository root, with `best.pt` downloaded into
`src/agritech/diagnosis/weights/` (see `weights/README.md`):

```bash
uv sync --group diagnosis

# Reading photos from a local folder: the file name is the uid
AGRITECH_PHOTO_DIR=/path/to/photos \
  uv run uvicorn agritech.diagnosis.mcp_server:create_app --factory --port 8078

# Tool time on the server, over HTTP (complement to H-T2, see docs/trials/ht2-diagnosis-time.md)
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

## Checkpoint and calibration

`best.pt` is the checkpoint written by `train.py` and read by
`model.load_checkpoint`, with `torch.load(weights_only=True)`. The server
uses its `classes`, `img_size` and `state_dict`.

`calibration.json` holds `temperature` (divides the scores before softmax)
and `threshold` (abstention threshold), both computed on the validation set.
Without it the model never abstains, and the server logs a warning.
