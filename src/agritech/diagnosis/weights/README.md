# Diagnosis model weights

| File | Content | Produced by |
| --- | --- | --- |
| `best.pt` | Trained MobileNetV3-Large on the 22 CCMT classes (contract in `../README.md`) | Training run `run1`, Diagnosis team |
| `calibration.json` | `temperature` and `threshold`, computed on the validation set | Calibration, sprint 2 (not yet available) |

Replacing `best.pt` changes every diagnosis: do it in its own pull request,
with the evaluation results of the new weights in the description.
