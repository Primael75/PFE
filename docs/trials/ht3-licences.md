# H-T3: licences of the retained datasets (photo diagnosis)

**Hypothesis (specification):** "The licences of the retained datasets allow
our use."

**Verdict: passed.** CCMT, the only photo dataset retained, is under CC BY
4.0. One point remains open on the pre-trained weights (see below).

## Datasets

| Dataset | Used | Licence | Proof | Checked on | Obligation |
| --- | --- | --- | --- | --- | --- |
| CCMT (Ghana) | yes: training, validation, test | CC BY 4.0 | licence shown on the [Mendeley page](https://data.mendeley.com/datasets/bwh3zbpkpv/1) | 2026-11-21 | cite Mensah et al. (2023), *Data in Brief*, 49, 109306 |

Data sheet: `docs/data/ccmt.md`.

## Libraries used by the photo diagnosis

Requirement ENF-11: no AGPL or non-commercial dependency in the served code.

| Library | Licence |
| --- | --- |
| PyTorch | BSD-3-Clause (with components under permissive licences) |
| torchvision | BSD-3-Clause |
| NumPy | BSD-3-Clause |
| Pillow | MIT-CMU |
| scikit-learn | BSD-3-Clause |
| ONNX | Apache-2.0 |
| ONNX Runtime, ONNX Runtime Web | MIT |

None is AGPL or non-commercial. Each one is recorded in `DEPENDANCES.md` when
it enters `pyproject.toml`.

## Open point: pre-trained weights

The model starts from MobileNetV3-Large weights trained on ImageNet
(torchvision). The [torchvision documentation](https://docs.pytorch.org/vision/stable/models)
states: "The pre-trained models provided in this library may have their own
licenses or terms and conditions derived from the dataset used for training.
It is your responsibility to determine whether you have permission to use the
models for your use case."

The ImageNet terms of use must be read before any commercial use of the model
(licence risk and ENF-11).
