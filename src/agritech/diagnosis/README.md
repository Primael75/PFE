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
`docs/trials/ht2-latency.md`). Not yet exposed as an MCP tool.

| Module | Role |
| --- | --- |
| `model.py` | MobileNetV3-Large, preprocessing contract, dataset, checkpoint loading |
| `train.py` | Two-stage training; reads `train.csv` and `val.csv` only |
| `evaluate.py` | Precision, recall and F1 per class on the validation split |
| `latency.py` | Response time per photo with PyTorch (reference for H-T2) |

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
