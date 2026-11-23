# Diagnosis model weights

The weights are kept out of Git (17 MB binary, ignored by `.gitignore`).
Download `best.pt` from the team's shared Drive, Diagnosis folder, into this
directory, or point `AGRITECH_DIAGNOSIS_MODEL` to it. Ask the Diagnosis team
for the link: it is not written here because the repository is public.

| File | Content | Produced by |
| --- | --- | --- |
| `best.pt` | Trained MobileNetV3-Large on the 22 CCMT classes (contract in `../README.md`) | Training run `run1`, Diagnosis team |
| `calibration.json` | `temperature` and `threshold`, computed on the validation set | Calibration, sprint 2 (not yet available) |

Replacing `best.pt` on the Drive changes every diagnosis: announce it in a
pull request that updates this table, with the evaluation results of the new
weights in the description.
